<template>
  <tr>
    <td>
      <v-menu offset-y content-class="menu-with-gap">
        <template v-slot:activator="{ on }">
          <span v-on="on" style="cursor: pointer">
            <v-avatar rounded :color="'#' + timeline.color" size="24" class="mr-2"> </v-avatar>
            {{ timeline.name }}
          </span>
        </template>
        <v-card width="300">
          <v-list>
            <v-list-item>
              <v-list-item-action>
                <v-icon>mdi-square-edit-outline</v-icon>
              </v-list-item-action>
              <v-list-item-subtitle>Rename timeline</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <v-list-item-action>
                <v-icon>mdi-magnify</v-icon>
              </v-list-item-action>
              <v-list-item-subtitle>
                <router-link style="text-decoration: none" :to="{ name: 'Explore', query: { timeline: timeline.id } }">
                  Explore this timeline
                </router-link>
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item @click="removeChip(chip)">
              <v-list-item-action>
                <v-icon>mdi-delete</v-icon>
              </v-list-item-action>
              <v-list-item-subtitle>Remove from sketch</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-menu>
    </td>
    <td>
      <ts-timeline-status-information
        :timeline="timeline"
        
      ></ts-timeline-status-information>
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
import TsTimelineStatusInformation from './TimelineStatusInformation'

export default {
  props: ['timeline'],
  components: {
    TsTimelineStatusInformation,
  },
  data() {
    return {
      timelineStatus: null,
      autoRefresh: false,
      indexedEvents: 0,
      totalEvents: null,
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
    remainingTime() {
      let t = new Date()
      let tNow = t.getTime() / 1000
      t = new Date(this.timeline.created_at)
      let t0 = t.getTime() / 1000
      let deltaNow = tNow - t0
      let deltaX = (100 * deltaNow) / this.indexedPercentage
      let tEnd = deltaX + t0

      return this.secondsToString(Math.floor(tEnd - tNow))
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
    },
  },
  created() {
    this.timelineStatus = this.timeline.status[0].status
    if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
      console.log("created -> THAT'S WEIRD")
      this.autoRefresh = true
    } else {
      this.autoRefresh = false
      this.indexedEvents = this.meta.stats_per_timeline[this.timeline.id]['count']
    }
  },
  methods: {
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then((response) => {
          this.timelineStatus = response.data.objects[0].status[0].status
          console.log(this.timelineStatus)
          this.indexedEvents = response.data.meta.lines_indexed
          this.totalEvents = JSON.parse(response.data.objects[0].total_events)
          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
            console.log('fetch data --> autorefresh true')
            this.autoRefresh = true
          } else {
            this.autoRefresh = false
          }
          this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
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
    secondsToString(d) {
      d = Number(d)
      var h = Math.floor(d / 3600)
      var m = Math.floor((d % 3600) / 60)
      var s = Math.floor((d % 3600) % 60)

      var hDisplay = h > 0 ? h + (h == 1 ? ' hour, ' : ' hours, ') : ''
      var mDisplay = m > 0 ? m + (m == 1 ? ' minute, ' : ' minutes, ') : ''
      var sDisplay = s > 0 ? s + (s == 1 ? ' second' : ' seconds') : ''
      return hDisplay + mDisplay + sDisplay
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
              console.log('autoRefresh watch')
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
.blink {
  animation: blinker 1s linear infinite;
  background-color: #f5f5f5;
}
@keyframes blinker {
  50% {
    opacity: 40%;
  }
}
</style>
