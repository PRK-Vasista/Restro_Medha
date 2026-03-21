const queue = [];

export function enqueue(event) {
  queue.push(event);
}

export function drain(sendFn) {
  const copy = [...queue];
  queue.length = 0;
  return Promise.all(copy.map(sendFn));
}

export function size() {
  return queue.length;
}
