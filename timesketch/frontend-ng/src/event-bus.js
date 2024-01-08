import Vue from 'vue'

// Create global EventBus to use in certain situations where performance is
// important and props/events are not optimal. Use with caution to not add
// unnecessary complexity.
const EventBus = new Vue()
export default EventBus
