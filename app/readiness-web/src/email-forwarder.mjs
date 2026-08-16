export async function forwardHelloEmail(message, env) {
  if (String(message.to).toLowerCase() !== 'hello@bflabs.cn') {
    message.reject('Unknown BFLabs recipient');
    return;
  }
  if (!env.PRIMARY_EMAIL_DESTINATION) throw new Error('PRIMARY_EMAIL_DESTINATION is not configured');

  const tasks = [message.forward(env.PRIMARY_EMAIL_DESTINATION)];
  if (env.SECONDARY_EMAIL_DESTINATION) tasks.push(message.forward(env.SECONDARY_EMAIL_DESTINATION));
  const results = await Promise.allSettled(tasks);
  if (results[0].status === 'rejected') throw results[0].reason;
  if (results[1]?.status === 'rejected') {
    console.warn('secondary_email_forward_failed', { name: results[1].reason?.name || 'Error' });
  }
}
