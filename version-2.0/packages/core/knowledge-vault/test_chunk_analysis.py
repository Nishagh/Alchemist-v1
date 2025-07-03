#!/usr/bin/env python3
"""
Test script for chunk analysis functionality
"""

import sys
import os

from services.chunk_analysis_service import ChunkAnalysisService

def test_chunk_analysis():
    """Test the chunk analysis service with a known file ID"""
    
    # Test file ID from the API response
    test_file_id = "5087e729-aae7-4c8a-8432-586f21261dad"
    
    print(f"Testing chunk analysis for file: {test_file_id}")
    
    try:
        # Initialize the service
        chunk_service = ChunkAnalysisService()
        
        # Run the analysis
        result = chunk_service.analyze_file_chunks(test_file_id)
        
        print("Analysis successful!")
        print(f"Total chunks: {result.get('total_chunks', 0)}")
        print(f"File: {result.get('filename', 'Unknown')}")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print("Content distribution:", result.get('content_distribution', {}))
            print("Quality metrics:", result.get('quality_metrics', {}))
            print("Optimization recommendations:", len(result.get('optimization_recommendations', [])))
        
        return result
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_chunk_analysis()