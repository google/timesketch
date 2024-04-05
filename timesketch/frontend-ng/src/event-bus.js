// import * as Vue from 'vue'

// const EventBus = new Vue()
// export default EventBus

import emitter from 'tiny-emitter/instance'

// Create global EventBus to use in certain situations where performance is
// important and props/events are not optimal. Use with caution to not add
// unnecessary complexity.
export default {
  $on: (...args) => emitter.on(...args),
  $once: (...args) => emitter.once(...args),
  $off: (...args) => emitter.off(...args),
  $emit: (...args) => emitter.emit(...args)
}
