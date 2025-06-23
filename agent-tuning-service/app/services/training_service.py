"""
Training service for managing fine-tuning jobs and data processing
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import openai
import structlog

from app.config.settings import get_settings
from app.models import (
    TrainingJob, TrainingPair, TrainingJobConfig, JobStatus, 
    TrainingDataValidation, ProcessTrainingDataResponse,
    ModelProvider, TrainingDataFormat
)
from app.services.firebase_service import FirebaseService

logger = structlog.get_logger(__name__)


class TrainingService:
    """Service for managing training jobs and data processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_service = FirebaseService()
        self.openai_client: Optional[openai.AsyncOpenAI] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the training service"""
        if self._initialized:
            return
        
        try:
            # Initialize Firebase service
            await self.firebase_service.initialize()
            
            # Initialize OpenAI client
            if self.settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                    organization=self.settings.openai_organization,
                    base_url=self.settings.openai_base_url
                )
            
            self._initialized = True
            logger.info("Training service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize training service", error=str(e))
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Training service not initialized. Call initialize() first.")
    
    async def validate_training_data(self, training_pairs: List[TrainingPair]) -> TrainingDataValidation:
        """Validate training data quality and format"""
        self._ensure_initialized()
        
        issues = []
        warnings = []
        recommendations = []
        valid_pairs = 0
        
        # Basic validation
        if len(training_pairs) < self.settings.min_training_pairs:
            issues.append(f"Insufficient training data. Need at least {self.settings.min_training_pairs} pairs, got {len(training_pairs)}")
        
        if len(training_pairs) > self.settings.max_training_pairs:
            issues.append(f"Too many training pairs. Maximum {self.settings.max_training_pairs} allowed, got {len(training_pairs)}")
        
        # Content validation
        for i, pair in enumerate(training_pairs):
            pair_issues = []
            
            # Check content length
            if len(pair.query) < 10:
                pair_issues.append(f"Query too short (pair {i+1})")
            if len(pair.response) < 10:
                pair_issues.append(f"Response too short (pair {i+1})")
            
            if len(pair.query) > 3000:
                warnings.append(f"Query very long in pair {i+1}, may affect training quality")
            if len(pair.response) > 3000:
                warnings.append(f"Response very long in pair {i+1}, may affect training quality")
            
            # Check for empty or repetitive content
            if pair.query.strip() == pair.response.strip():
                pair_issues.append(f"Query and response are identical (pair {i+1})")
            
            # Count valid pairs
            if not pair_issues:
                valid_pairs += 1
            else:
                issues.extend(pair_issues)
        
        # Quality recommendations
        if len(training_pairs) < 50:
            recommendations.append("Consider adding more training pairs (50+ recommended) for better model performance")
        
        if valid_pairs / len(training_pairs) < 0.8:
            recommendations.append("High number of invalid pairs detected. Review and clean training data")
        
        # Check diversity
        unique_queries = len(set(pair.query for pair in training_pairs))
        if unique_queries / len(training_pairs) < 0.7:
            recommendations.append("Low query diversity detected. Add more varied examples")
        
        query_types = set(pair.query_type for pair in training_pairs if pair.query_type)
        if len(query_types) < 3:
            recommendations.append("Limited query type diversity. Include various types of queries")
        
        is_valid = len(issues) == 0 and valid_pairs >= self.settings.min_training_pairs
        
        validation = TrainingDataValidation(
            is_valid=is_valid,
            total_pairs=len(training_pairs),
            valid_pairs=valid_pairs,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )
        
        logger.info(
            "Training data validated",
            total_pairs=len(training_pairs),
            valid_pairs=valid_pairs,
            is_valid=is_valid,
            issues_count=len(issues),
            warnings_count=len(warnings)
        )
        
        return validation
    
    async def process_training_data(
        self, 
        training_pairs: List[TrainingPair], 
        format: TrainingDataFormat = TrainingDataFormat.OPENAI_CHAT,
        agent_id: str = None
    ) -> ProcessTrainingDataResponse:
        """Process training data into required format"""
        self._ensure_initialized()
        
        # Validate data first
        validation = await self.validate_training_data(training_pairs)
        
        if not validation.is_valid:
            return ProcessTrainingDataResponse(
                validation=validation,
                processed_data_url=None
            )
        
        # Convert to required format
        if format == TrainingDataFormat.OPENAI_CHAT:
            processed_data = self._convert_to_openai_format(training_pairs)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Calculate size
        json_content = json.dumps(processed_data, indent=2)
        file_size = len(json_content.encode('utf-8'))
        
        # Store processed data if agent_id provided
        processed_data_url = None
        if agent_id:
            filename = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            processed_data_url = await self.firebase_service.upload_training_file(
                json_content.encode('utf-8'),
                filename,
                agent_id
            )
        
        # Estimate cost (rough OpenAI pricing)
        estimated_cost = self._estimate_training_cost(len(training_pairs), file_size)
        
        return ProcessTrainingDataResponse(
            validation=validation,
            processed_data_url=processed_data_url,
            file_size_bytes=file_size,
            estimated_cost=estimated_cost
        )
    
    def _convert_to_openai_format(self, training_pairs: List[TrainingPair]) -> List[Dict[str, Any]]:
        """Convert training pairs to OpenAI fine-tuning format"""
        formatted_data = []
        
        for pair in training_pairs:
            # OpenAI chat format
            formatted_pair = {
                "messages": [
                    {
                        "role": "user",
                        "content": pair.query
                    },
                    {
                        "role": "assistant", 
                        "content": pair.response
                    }
                ]
            }
            
            # Add metadata if available
            if pair.context or pair.query_type:
                formatted_pair["metadata"] = {
                    "query_type": pair.query_type,
                    "context": pair.context,
                    "timestamp": pair.timestamp.isoformat()
                }
            
            formatted_data.append(formatted_pair)
        
        return formatted_data
    
    def _estimate_training_cost(self, num_pairs: int, file_size_bytes: int) -> float:
        """Estimate training cost based on OpenAI pricing"""
        # Rough estimate based on OpenAI fine-tuning pricing
        # Actual costs may vary
        base_cost = 0.008  # per 1K tokens for training
        tokens_per_pair = 100  # rough estimate
        total_tokens = num_pairs * tokens_per_pair
        
        cost = (total_tokens / 1000) * base_cost
        return round(cost, 4)
    
    async def create_training_job(
        self, 
        agent_id: str, 
        user_id: str,
        job_name: str,
        description: Optional[str],
        config: TrainingJobConfig,
        training_pairs: List[TrainingPair]
    ) -> TrainingJob:
        """Create a new training job"""
        self._ensure_initialized()
        
        # Process and validate training data
        processed_response = await self.process_training_data(
            training_pairs, 
            config.training_format, 
            agent_id
        )
        
        if not processed_response.validation.is_valid:
            raise ValueError(f"Invalid training data: {', '.join(processed_response.validation.issues)}")
        
        # Store training data
        training_data_batch_id = await self.firebase_service.store_training_data(agent_id, training_pairs)
        
        # Create training job
        job = TrainingJob(
            id="",  # Will be set by Firebase
            agent_id=agent_id,
            user_id=user_id,
            job_name=job_name,
            description=description,
            status=JobStatus.PENDING,
            config=config,
            total_training_pairs=len(training_pairs),
            training_data_url=processed_response.processed_data_url,
            created_at=datetime.now(timezone.utc),
            cost_estimate=processed_response.estimated_cost
        )
        
        # Save to Firebase
        job_id = await self.firebase_service.create_training_job(job)
        job.id = job_id
        
        logger.info(
            "Training job created",
            job_id=job_id,
            agent_id=agent_id,
            pairs_count=len(training_pairs)
        )
        
        return job
    
    async def start_training_job(self, job_id: str) -> bool:
        """Start a training job"""
        self._ensure_initialized()
        
        job = await self.firebase_service.get_training_job(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        if job.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in pending status")
        
        try:
            # Update status to queued
            await self.firebase_service.update_training_job(job_id, {
                'status': JobStatus.QUEUED.value,
                'started_at': datetime.now(timezone.utc)
            })
            
            # Start training based on provider
            if job.config.model_provider == ModelProvider.OPENAI:
                await self._start_openai_training(job)
            else:
                raise ValueError(f"Unsupported provider: {job.config.model_provider}")
            
            logger.info("Training job started", job_id=job_id)
            return True
            
        except Exception as e:
            # Update job with error
            await self.firebase_service.update_training_job(job_id, {
                'status': JobStatus.FAILED.value,
                'error_message': str(e)
            })
            logger.error("Failed to start training job", job_id=job_id, error=str(e))
            raise
    
    async def _start_openai_training(self, job: TrainingJob):
        """Start OpenAI fine-tuning job"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        try:
            # Download training data
            training_data_content = await self.firebase_service.download_training_file(job.training_data_url)
            
            # Upload file to OpenAI
            file_response = await self.openai_client.files.create(
                file=training_data_content,
                purpose="fine-tune"
            )
            
            # Create fine-tuning job
            fine_tune_response = await self.openai_client.fine_tuning.jobs.create(
                training_file=file_response.id,
                model=job.config.base_model,
                hyperparameters={
                    "n_epochs": job.config.epochs,
                    "batch_size": job.config.batch_size,
                    "learning_rate_multiplier": job.config.learning_rate
                },
                suffix=job.config.suffix
            )
            
            # Update job with OpenAI job ID
            await self.firebase_service.update_training_job(job.id, {
                'status': JobStatus.RUNNING.value,
                'external_job_id': fine_tune_response.id,
                'progress_percentage': 0.0
            })
            
            logger.info(
                "OpenAI fine-tuning job started",
                job_id=job.id,
                openai_job_id=fine_tune_response.id
            )
            
        except Exception as e:
            logger.error("Failed to start OpenAI training", job_id=job.id, error=str(e))
            raise
    
    async def check_job_progress(self, job_id: str) -> bool:
        """Check and update job progress"""
        self._ensure_initialized()
        
        job = await self.firebase_service.get_training_job(job_id)
        if not job or not job.external_job_id:
            return False
        
        try:
            if job.config.model_provider == ModelProvider.OPENAI:
                return await self._check_openai_progress(job)
            else:
                raise ValueError(f"Unsupported provider: {job.config.model_provider}")
                
        except Exception as e:
            logger.error("Failed to check job progress", job_id=job_id, error=str(e))
            return False
    
    async def _check_openai_progress(self, job: TrainingJob) -> bool:
        """Check OpenAI fine-tuning job progress"""
        if not self.openai_client:
            return False
        
        try:
            # Get job status from OpenAI
            openai_job = await self.openai_client.fine_tuning.jobs.retrieve(job.external_job_id)
            
            # Map OpenAI status to our status
            status_mapping = {
                'validating_files': JobStatus.VALIDATING,
                'queued': JobStatus.QUEUED,
                'running': JobStatus.RUNNING,
                'succeeded': JobStatus.COMPLETED,
                'failed': JobStatus.FAILED,
                'cancelled': JobStatus.CANCELLED
            }
            
            new_status = status_mapping.get(openai_job.status, JobStatus.RUNNING)
            
            # Prepare updates
            updates = {
                'status': new_status.value,
                'progress_percentage': self._calculate_progress(openai_job)
            }
            
            # Handle completion
            if new_status == JobStatus.COMPLETED:
                updates.update({
                    'completed_at': datetime.now(timezone.utc),
                    'external_model_id': openai_job.fine_tuned_model,
                    'result_model_id': openai_job.fine_tuned_model,
                    'progress_percentage': 100.0
                })
                
                # Store model information
                await self._store_completed_model(job, openai_job)
            
            elif new_status == JobStatus.FAILED:
                updates['error_message'] = getattr(openai_job, 'error', {}).get('message', 'Training failed')
            
            # Update job
            await self.firebase_service.update_training_job(job.id, updates)
            
            logger.info(
                "Job progress updated",
                job_id=job.id,
                status=new_status.value,
                progress=updates['progress_percentage']
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to check OpenAI progress", job_id=job.id, error=str(e))
            return False
    
    def _calculate_progress(self, openai_job) -> float:
        """Calculate training progress percentage"""
        # OpenAI doesn't provide detailed progress, so we estimate
        status_progress = {
            'validating_files': 5.0,
            'queued': 10.0,
            'running': 50.0,  # Could be more sophisticated
            'succeeded': 100.0,
            'failed': 0.0,
            'cancelled': 0.0
        }
        
        return status_progress.get(openai_job.status, 0.0)
    
    async def _store_completed_model(self, job: TrainingJob, openai_job):
        """Store completed fine-tuned model information"""
        from app.models import FineTunedModel
        
        model = FineTunedModel(
            id="",  # Will be set by Firebase
            agent_id=job.agent_id,
            model_name=f"{job.job_name}_model",
            base_model=job.config.base_model,
            model_provider=job.config.model_provider,
            external_model_id=openai_job.fine_tuned_model,
            training_job_id=job.id,
            training_pairs_count=job.total_training_pairs,
            training_completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        await self.firebase_service.store_fine_tuned_model(model)
        
        logger.info(
            "Fine-tuned model stored",
            job_id=job.id,
            model_id=openai_job.fine_tuned_model
        )
    
    async def cancel_training_job(self, job_id: str) -> bool:
        """Cancel a training job"""
        self._ensure_initialized()
        
        job = await self.firebase_service.get_training_job(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        try:
            # Cancel external job if running
            if job.external_job_id and job.config.model_provider == ModelProvider.OPENAI:
                if self.openai_client:
                    await self.openai_client.fine_tuning.jobs.cancel(job.external_job_id)
            
            # Update job status
            await self.firebase_service.update_training_job(job_id, {
                'status': JobStatus.CANCELLED.value,
                'completed_at': datetime.now(timezone.utc)
            })
            
            logger.info("Training job cancelled", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("Failed to cancel training job", job_id=job_id, error=str(e))
            raise