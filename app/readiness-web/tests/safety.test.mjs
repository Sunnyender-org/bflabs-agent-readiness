import test from 'node:test';
import assert from 'node:assert/strict';
import { assertPublicHostname, isUnsafeAddress, normalizeTarget } from '../src/safety.mjs';

test('normalizes a public hostname to HTTPS origin', () => {
  assert.equal(normalizeTarget('example.com/pricing').toString(), 'https://example.com/');
});

test('rejects credentials, unsafe schemes, ports, and IP literals', () => {
  for (const input of [
    'file:///etc/passwd',
    'https://user:pass@example.com',
    'https://example.com:8443',
    'http://127.0.0.1',
    'http://[::1]',
    'localhost',
  ]) {
    assert.throws(() => normalizeTarget(input));
  }
});

test('recognizes private, reserved, link-local, and documentation addresses', () => {
  for (const address of ['10.0.0.1', '172.16.1.1', '192.168.1.1', '169.254.1.2', '127.0.0.1', '203.0.113.8', '::1', 'fc00::1', 'fe80::1', '2001:db8::1']) {
    assert.equal(isUnsafeAddress(address), true, address);
  }
  assert.equal(isUnsafeAddress('1.1.1.1'), false);
  assert.equal(isUnsafeAddress('2606:4700:4700::1111'), false);
});

test('rejects a hostname when any resolved address is unsafe', async () => {
  const lookup = async () => [{ address: '1.1.1.1', family: 4 }, { address: '127.0.0.1', family: 4 }];
  await assert.rejects(() => assertPublicHostname('example.com', lookup), /不安全地址/);
});
