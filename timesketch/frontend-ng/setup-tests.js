// Components read the bare localStorage global from data(), which happy-dom
// does not define. Without this the component throws before the test body runs.
if (typeof globalThis.localStorage === 'undefined') {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
  }
}

const node = document.createElement("meta");
node.textContent = 'test';
document.body.appendChild(node);
