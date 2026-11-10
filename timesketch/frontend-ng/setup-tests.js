// Ensure happy-dom's Node.prototype.nodeName delegates to subclass getters
// so DOMPurify >= 3.4.16 (which caches Node.prototype's nodeName getter) works in tests.
const origNodeNameDesc = Object.getOwnPropertyDescriptor(window.Node.prototype, 'nodeName')
if (origNodeNameDesc && origNodeNameDesc.get) {
  Object.defineProperty(window.Node.prototype, 'nodeName', {
    configurable: true,
    get() {
      let proto = Object.getPrototypeOf(this)
      while (proto && proto !== window.Node.prototype) {
        const desc = Object.getOwnPropertyDescriptor(proto, 'nodeName')
        if (desc && desc.get) return desc.get.call(this)
        proto = Object.getPrototypeOf(proto)
      }
      return origNodeNameDesc.get.call(this)
    },
  })
}

const node = document.createElement("meta");
node.textContent = 'test';
document.body.appendChild(node);
