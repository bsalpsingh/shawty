import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 50 },  // Ramp up to 50 concurrent users
    { duration: '30s', target: 100 }, // Ramp up to 100 concurrent users
    { duration: '30s', target: 100 }, // Stay at 100 users to watch stability
    { duration: '15s', target: 0 },   // Scale down
  ],
};

// Simulated short codes that exist in your database
const testCodes = ['5D2XY9', '2Joh83', '4E5tT9', '2tjxEy'];

export default function () {
  // Pick a random short code from the array
  const shortCode = testCodes[Math.floor(Math.random() * testCodes.length)];
  
  // Target your running FastAPI server
  const url = `http://localhost:8000/${shortCode}`;
  
  const params = {
    redirects: 0, // IMPORTANT: Prevents k6 from following the redirect to the target website
  };

  const res = http.get(url, params);

  check(res, {
    'is redirect (302/307)': (r) => r.status === 302 || r.status === 307,
    'under 200ms': (r) => r.timings.duration < 200,
  });

  // Short sleep to simulate real user pacing (adjust or remove to stress test completely)
  sleep(0.05); 
}


// k6 run load-test.js
