import dayjs from 'dayjs'

// Add plugins
import utc from 'dayjs/plugin/utc'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/utc'

dayjs.extend(utc)
dayjs.extend(relativeTime)
dayjs.extend(duration)

export default dayjs
