<template>
  <tr>
    <td>
      <ts-timeline-chip
        :timeline="timeline"
        :is-selected="true"
        :events-count="0"
      ></ts-timeline-chip>
    </td>
    <td>{{ indexedEvents | compactNumber }}</td>
    <td>{{ timeline.user.username }}</td>
    <td>
      {{ timeline.created_at | shortDateTime }} <small>({{ timeline.created_at | timeSince }})</small>
    </td>
  </tr>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsTimelineChip from './Explore/TimelineChip'

export default {
  props: ['timeline'],
  components: {
    TsTimelineChip,
  },
  data() {
    return {
      timelineStatus: null,
      autoRefresh: false,
      indexedEvents: 0,
      totalEvents: null,
      dialogStatus: false,
      datasources: [],
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    sketch() {
      return this.$store.state.sketch
    },
    indexedPercentage() {
      let totalEvents = 1
      if (this.totalEvents) {
        totalEvents = this.totalEvents.total
      }
      let percentage = this.indexedEvents / totalEvents
      return Math.min(Math.floor(percentage * 100), 100)
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
    },
    iconStatus() {
      if (this.timelineStatus === 'ready') return 'mdi-check-circle'
      if (this.timelineStatus === 'processing') return 'mdi-circle-slice-7'
      return 'mdi-alert-circle'
    },
  },
  created() {
    this.timelineStatus = this.timeline.status[0].status
    if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
      this.autoRefresh = true
      this.fetchData()
    } else {
      this.autoRefresh = false
      this.indexedEvents = this.meta.stats_per_timeline[this.timeline.id]['count']
    }
  },
  methods: {
    closeDialogStatus() {
      this.dialogStatus = false
    },
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then((response) => {
          this.timelineStatus = response.data.objects[0].status[0].status
          this.indexedEvents = response.data.meta.lines_indexed
          this.totalEvents = JSON.parse(response.data.objects[0].total_events)
          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
            this.autoRefresh = true
          } else {
            this.autoRefresh = false
            this.$store.dispatch('updateSketch', this.sketch.id)
          }
        })
        .catch((e) => {})
    },
    timelineStatusColors() {
      if (this.timelineStatus === 'ready') {
        return 'info'
      } else if (this.timelineStatus === 'processing') {
        return 'warning'
      }
      // status = fail
      return 'error'
    },
  },
  beforeDestroy() {
    clearInterval(this.t)
    this.t = false
  },
  watch: {
    autoRefresh(val) {
      if (val && !this.t) {
        this.t = setInterval(
          function () {
            this.fetchData()
            if (this.timelineStatus === 'ready' || this.timelineStatus === 'fail') {
              this.autoRefresh = false
            }
          }.bind(this),
          5000
        )
      } else {
        clearInterval(this.t)
        this.t = false
      }
    },
  },
}
</script>

<style scoped lang="scss">
@keyframes blinker {
  50% {
    opacity: 40%;
  }
}
</style>
