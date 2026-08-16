import assert from 'node:assert/strict';
import test from 'node:test';
import { forwardHelloEmail } from '../src/email-forwarder.mjs';

test('hello mail forwards to both configured destinations', async () => {
  const forwarded = [];
  await forwardHelloEmail({
    to: 'hello@bflabs.cn',
    forward: async (destination) => forwarded.push(destination),
    reject: () => assert.fail('hello must not be rejected'),
  }, {
    PRIMARY_EMAIL_DESTINATION: 'primary@example.com',
    SECONDARY_EMAIL_DESTINATION: 'secondary@example.com',
  });
  assert.deepEqual(forwarded, ['primary@example.com', 'secondary@example.com']);
});

test('unknown recipients are rejected without forwarding', async () => {
  let rejected = false;
  await forwardHelloEmail({
    to: 'other@bflabs.cn',
    forward: async () => assert.fail('unknown recipient must not forward'),
    reject: () => { rejected = true; },
  }, { PRIMARY_EMAIL_DESTINATION: 'primary@example.com' });
  assert.equal(rejected, true);
});
