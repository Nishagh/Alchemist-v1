/**
 * Credits Middleware
 * 
 * Middleware for checking and deducting credits for API usage
 */

const { creditsService } = require('../services/creditsService');

/**
 * Middleware to check credits before API usage
 * This ensures users have sufficient credits before processing requests
 */
const checkCreditsBeforeUsage = async (req, res, next) => {
  try {
    if (!req.user) {
      return next(); // Skip if no authenticated user
    }
    
    const userId = req.user.uid;
    
    // Estimate credit cost based on request
    const estimatedCost = estimateRequestCost(req);
    
    if (estimatedCost > 0) {
      // Check if user has sufficient credits
      const hasSufficientCredits = await creditsService.hasSufficientCredits(userId, estimatedCost);
      
      if (!hasSufficientCredits) {
        const balance = await creditsService.getUserBalance(userId);
        
        return res.status(402).json({
          success: false,
          error: 'Insufficient credits',
          error_code: 'INSUFFICIENT_CREDITS',
          details: {
            required_credits: estimatedCost,
            available_credits: balance.total_credits,
            message: 'Please purchase credits to continue using the service'
          },
          actions: {
            purchase_credits: '/billing',
            view_packages: '/api/credits/packages'
          }
        });
      }
      
      // Add estimated cost to request for later deduction
      req.estimatedCreditCost = estimatedCost;
    }
    
    next();
  } catch (error) {
    console.error('Error checking credits:', error);
    // Don't block the request if credit check fails
    next();
  }
};

/**
 * Middleware to deduct credits after successful API usage
 * This runs after the API response is generated
 */
const deductCreditsAfterUsage = (req, res, next) => {
  // Store original res.json to intercept response
  const originalJson = res.json;
  
  res.json = function(data) {
    // Call original json method
    const result = originalJson.call(this, data);
    
    // Deduct credits asynchronously (don't block response)
    if (res.statusCode < 400 && req.user) {
      setImmediate(async () => {
        try {
          await deductCreditsFromResponse(req, data);
        } catch (error) {
          console.error('Error deducting credits:', error);
          // Log the error but don't fail the request
        }
      });
    }
    
    return result;
  };
  
  next();
};

/**
 * Extract actual usage and deduct credits
 */
async function deductCreditsFromResponse(req, responseData) {
  try {
    const userId = req.user.uid;
    let characters = 0;
    let agentId = null;
    let serviceType = 'api_usage';
    
    // Calculate actual character usage from response
    if (responseData) {
      // For agent interaction responses
      if (responseData.response && typeof responseData.response === 'string') {
        characters += responseData.response.length;
        serviceType = 'agent_interaction';
      }
      
      // For batch responses
      if (responseData.responses && Array.isArray(responseData.responses)) {
        characters += responseData.responses.reduce((total, response) => {
          return total + (typeof response === 'string' ? response.length : 0);
        }, 0);
        serviceType = 'batch_processing';
      }
      
      // For knowledge base responses
      if (responseData.results && Array.isArray(responseData.results)) {
        characters += JSON.stringify(responseData.results).length;
        serviceType = 'knowledge_base_search';
      }
      
      // Extract agent ID from request or response
      agentId = req.params.agentId || req.body.agent_id || responseData.agent_id;
    }
    
    // Also count input characters
    if (req.body) {
      if (req.body.message && typeof req.body.message === 'string') {
        characters += req.body.message.length;
      }
      
      if (req.body.prompt && typeof req.body.prompt === 'string') {
        characters += req.body.prompt.length;
      }
      
      if (req.body.content && typeof req.body.content === 'string') {
        characters += req.body.content.length;
      }
      
      if (req.body.query && typeof req.body.query === 'string') {
        characters += req.body.query.length;
      }
    }
    
    // Calculate credit cost
    const creditCost = creditsService.calculateCharacterCost(characters);
    
    // Add base API call cost
    const totalCost = creditCost + creditsService.constants.API_CALL_COST;
    
    // Deduct credits if usage detected
    if (totalCost > 0) {
      const usageDetails = {
        characters,
        tokens: 0, // Can be extended for token-based models
        api_calls: 1,
        agent_id: agentId,
        cost_per_unit: 1 / creditsService.constants.CHARACTERS_PER_CREDIT,
        service_type: serviceType,
        description: `${serviceType} - ${characters} characters`,
        endpoint: `${req.method} ${req.path}`,
        timestamp: new Date().toISOString()
      };
      
      const result = await creditsService.deductCredits(userId, totalCost, usageDetails);
      
      console.log(`Credits deducted: ${totalCost.toFixed(4)} (${characters} chars) for user ${userId}${agentId ? ` agent: ${agentId}` : ''}`);
      
      // Check for low balance alert
      const lowBalanceCheck = await creditsService.checkLowBalanceAlert(userId);
      if (lowBalanceCheck.should_alert) {
        console.log(`Low balance alert for user ${userId}: ${lowBalanceCheck.current_balance} credits remaining`);
        // TODO: Send notification to user
      }
      
      return result;
    }
  } catch (error) {
    if (error.message?.includes('Insufficient credits')) {
      console.warn(`Credits exhausted during request for user ${req.user.uid}`);
      // User ran out of credits mid-request - this should be rare due to pre-check
    } else {
      console.error('Error in deductCreditsFromResponse:', error);
    }
    throw error;
  }
}

/**
 * Estimate credit cost for a request before processing
 */
function estimateRequestCost(req) {
  let estimatedCharacters = 0;
  
  // Estimate based on request body
  if (req.body) {
    if (req.body.message) estimatedCharacters += req.body.message.length;
    if (req.body.prompt) estimatedCharacters += req.body.prompt.length;
    if (req.body.content) estimatedCharacters += req.body.content.length;
    if (req.body.query) estimatedCharacters += req.body.query.length;
  }
  
  // Add estimated response size (conservative estimate)
  const estimatedResponseSize = Math.max(estimatedCharacters * 2, 500); // At least 500 chars response
  const totalEstimatedChars = estimatedCharacters + estimatedResponseSize;
  
  // Calculate credit cost
  const characterCost = totalEstimatedChars / creditsService.constants.CHARACTERS_PER_CREDIT;
  const apiCallCost = creditsService.constants.API_CALL_COST;
  
  return characterCost + apiCallCost;
}

/**
 * Middleware for admin operations (bypass credit checks)
 */
const bypassCreditsForAdmin = (req, res, next) => {
  // Mark request as admin to bypass credit checks
  req.adminBypass = true;
  next();
};

/**
 * Manual credit deduction utility
 */
const manualDeductCredits = async (userId, amount, description, details = {}) => {
  try {
    const usageDetails = {
      characters: 0,
      tokens: 0,
      api_calls: 0,
      ...details,
      service_type: 'manual_deduction',
      description: description,
      timestamp: new Date().toISOString()
    };
    
    return await creditsService.deductCredits(userId, amount, usageDetails);
  } catch (error) {
    console.error('Error in manual credit deduction:', error);
    throw error;
  }
};

/**
 * Get user's current credit status for middleware
 */
const getUserCreditStatus = async (userId) => {
  try {
    const [balance, lowBalanceCheck] = await Promise.all([
      creditsService.getUserBalance(userId),
      creditsService.checkLowBalanceAlert(userId)
    ]);
    
    return {
      balance: balance.total_credits,
      available_credits: balance.available_credits,
      bonus_credits: balance.bonus_credits,
      is_low_balance: lowBalanceCheck.is_low_balance,
      low_balance_threshold: lowBalanceCheck.threshold,
      can_use_api: balance.total_credits > 0
    };
  } catch (error) {
    console.error('Error getting user credit status:', error);
    return {
      balance: 0,
      can_use_api: false,
      is_low_balance: true
    };
  }
};

module.exports = {
  checkCreditsBeforeUsage,
  deductCreditsAfterUsage,
  bypassCreditsForAdmin,
  manualDeductCredits,
  getUserCreditStatus
};

// For ES6 import compatibility
module.exports.default = module.exports;