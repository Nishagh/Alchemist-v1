/**
 * Usage Tracking Middleware
 * 
 * Automatically tracks API usage for billing purposes
 */

const { billingService } = require('../services/billingService');

/**
 * Middleware to track character usage
 * This should be added to agent interaction endpoints
 */
const trackCharacterUsage = (req, res, next) => {
  // Store original res.json to intercept response
  const originalJson = res.json;
  
  res.json = function(data) {
    // Call original json method
    const result = originalJson.call(this, data);
    
    // Track usage asynchronously (don't block response)
    if (res.statusCode < 400 && req.user) {
      setImmediate(async () => {
        try {
          await trackUsageFromResponse(req, data);
        } catch (error) {
          console.error('Error tracking usage:', error);
          // Don't fail the request if usage tracking fails
        }
      });
    }
    
    return result;
  };
  
  next();
};

/**
 * Extract usage data from response and track it
 */
async function trackUsageFromResponse(req, responseData) {
  try {
    const userId = req.user.uid;
    let characters = 0;
    let agentId = null;
    
    // Extract character count from different response types
    if (responseData) {
      // For agent interaction responses
      if (responseData.response && typeof responseData.response === 'string') {
        characters += responseData.response.length;
      }
      
      // For batch responses
      if (responseData.responses && Array.isArray(responseData.responses)) {
        characters += responseData.responses.reduce((total, response) => {
          return total + (typeof response === 'string' ? response.length : 0);
        }, 0);
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
    }
    
    // Track usage if we have characters to track
    if (characters > 0) {
      await billingService.trackCharacterUsage(userId, characters, agentId);
      console.log(`Tracked ${characters} characters for user ${userId}${agentId ? ` (agent: ${agentId})` : ''}`);
    }
  } catch (error) {
    console.error('Error in trackUsageFromResponse:', error);
    throw error;
  }
}

/**
 * Middleware to track API calls
 */
const trackApiCall = async (req, res, next) => {
  if (req.user) {
    // Track API call asynchronously
    setImmediate(async () => {
      try {
        const userId = req.user.uid;
        // You can extend this to track different types of API calls
        console.log(`API call tracked for user ${userId}: ${req.method} ${req.path}`);
      } catch (error) {
        console.error('Error tracking API call:', error);
      }
    });
  }
  next();
};

/**
 * Middleware to check usage limits before processing request
 */
const checkUsageLimits = async (req, res, next) => {
  try {
    if (!req.user) {
      return next();
    }
    
    const userId = req.user.uid;
    
    // Get current usage and subscription
    const [usage, subscription] = await Promise.all([
      billingService.getCurrentUsage(userId),
      billingService.getUserSubscription(userId)
    ]);
    
    // Check monthly character limit
    const charactersUsed = usage.metrics?.characters_used || 0;
    const charactersLimit = subscription.limits?.characters_per_month || 1000000;
    
    if (charactersLimit > 0 && charactersUsed >= charactersLimit) {
      return res.status(429).json({
        success: false,
        error: 'Monthly character limit exceeded',
        details: {
          used: charactersUsed,
          limit: charactersLimit,
          resetDate: subscription.billing?.next_billing_date
        }
      });
    }
    
    // Check spending limit
    const totalCost = usage.costs?.total_cost || 0;
    const costLimit = 1000; // Default monthly limit in INR
    
    if (totalCost >= costLimit) {
      return res.status(429).json({
        success: false,
        error: 'Monthly spending limit exceeded',
        details: {
          spent: totalCost,
          limit: costLimit,
          currency: 'INR'
        }
      });
    }
    
    // Add usage info to request for potential use in handlers
    req.usageInfo = {
      charactersUsed,
      charactersLimit,
      totalCost,
      costLimit,
      subscription
    };
    
    next();
  } catch (error) {
    console.error('Error checking usage limits:', error);
    // Don't block request if limit check fails
    next();
  }
};

/**
 * Utility function to manually track usage
 * Can be called from any route handler
 */
const manualTrackUsage = async (userId, characters, agentId = null) => {
  try {
    return await billingService.trackCharacterUsage(userId, characters, agentId);
  } catch (error) {
    console.error('Error in manual usage tracking:', error);
    throw error;
  }
};

module.exports = {
  trackCharacterUsage,
  trackApiCall,
  checkUsageLimits,
  manualTrackUsage
};

// For ES6 import compatibility
module.exports.default = module.exports;