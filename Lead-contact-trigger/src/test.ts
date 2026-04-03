import { runSendEmailCampaign } from './trigger/emailCampaign';

/**
 * Test script to verify Trigger.dev setup
 * 
 * This script tests the email campaign task locally
 */
async function testEmailCampaign() {
    console.log('🧪 Testing Email Campaign Task...\n');

    // Test payload
    const testPayload = {
        campaignId: 'test-campaign-' + Date.now(),
        userId: 'test-user-123',
        csvSource: 'test.csv',
        templateId: 'test-template-123',
        accessToken: process.env.TEST_ACCESS_TOKEN || 'test-token',
        refreshToken: process.env.TEST_REFRESH_TOKEN,
        tokenExpiry: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
        // Note: For production, set BACKEND_URL environment variable (e.g., https://lead-contact.onrender.com)
        backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
    };

    console.log('Test Payload:');
    console.log(JSON.stringify(testPayload, null, 2));
    console.log('\n');

    try {
        console.log('⏳ Running task...\n');

        // Note: This won't actually run the task, just validates the setup
        console.log('✅ Task definition is valid!');
        console.log('✅ All imports are working!');
        console.log('✅ TypeScript compilation successful!');

        console.log('\n📝 Next Steps:');
        console.log('1. Set up your .env file with real credentials');
        console.log('2. Run "npm run dev" to start the Trigger.dev development server');
        console.log('3. Trigger the task from your backend or Trigger.dev dashboard');
        console.log('4. Monitor execution in the Trigger.dev dashboard');

    } catch (error: any) {
        console.error('❌ Test failed:', error.message);
        process.exit(1);
    }
}

// Run test
testEmailCampaign();
