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
      <v-dialog v-model="dialog" width="600">
        <template v-slot:activator="{ on, attrs }">
          <small v-bind="attrs" v-on="on">
            <v-icon v-if="timelineStatus === 'ready'">mdi-check-circle</v-icon>
            <v-progress-circular
              v-if="timelineStatus === 'processing'"
              :rotate="360"
              :size="30"
              :width="7"
              :value="indexedPercentage"
              color="teal"
            >
            </v-progress-circular>
            <v-icon v-if="timelineStatus === 'fail'">mdi-check-circle</v-icon>
          </small>
        </template>

        <v-card>
          <v-app-bar flat dense>Detailed information for: {{ timeline.name }}</v-app-bar>
          <v-card-text class="pa-5">
            <ul style="list-style-type: none">
              <li><strong>Opensearch index: </strong>{{ timeline.searchindex.index_name }}</li>
              <li>
                <strong v-if="timelineStatus === 'ready'">Number of events: </strong>
                <strong v-if="timelineStatus === 'processing'">Number of indexed events: </strong>
                {{ indexedEvents | compactNumber }} ({{ indexedEvents }})
              </li>
              <li><strong>Created by: </strong>{{ timeline.user.username }}</li>
              <li>
                <strong>Created at: </strong>{{ timeline.created_at | shortDateTime }}
                <small>({{ timeline.created_at | timeSince }})</small>
              </li>
            </ul>

            <br /><br />
            <v-alert
              v-for="datasource in timeline.datasources"
              :key="datasource.id"
              colored-border
              border="left"
              elevation="1"
              :type="timelineStatusColors()"
            >
              <ul style="list-style-type: none">
                <li>
                  <strong>Events:</strong>
                  <ul>
                    <li v-for="(numberEvents, type) in totalEvents" :key="type">
                      <strong>{{ type }}</strong
                      >: {{ numberEvents | compactNumber }}
                    </li>
                  </ul>
                </li>
                <li v-if="timelineStatus === 'processing'">
                  <strong>Percentage Completed</strong> {{ indexedPercentage }} %
                </li>
                <li v-if="timelineStatus === 'processing'"><strong>Remaining time:</strong> {{ remainingTime }}</li>

                <li v-if="timelineStatus !== 'processing'"><strong>Provider:</strong> {{ datasource.provider }}</li>
                <li v-if="timelineStatus !== 'processing'"><strong>Context:</strong> {{ datasource.context }}</li>
                <li v-if="timelineStatus !== 'processing'">
                  <strong>File on disk:</strong> {{ datasource.file_on_disk }}
                </li>
                <li v-if="timelineStatus !== 'processing'">
                  <strong>File size:</strong> {{ datasource.file_size | compactBytes }}
                </li>
                <li v-if="timelineStatus !== 'processing'">
                  <strong>Original filename:</strong> {{ datasource.original_filename }}
                </li>
                <li v-if="timelineStatus !== 'processing'"><strong>Data label:</strong> {{ datasource.data_label }}</li>
              </ul>
              <br />
            </v-alert>
          </v-card-text>
          <v-progress-linear
            v-if="timelineStatus === 'processing'"
            color="light-blue"
            height="10"
            :value="indexedPercentage"
            striped
          ></v-progress-linear>
          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="dialog = false"> Close </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
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

export default {
  props: ['timeline'],
  data() {
    return {
      dialog: false,
      timelineStatus: null,
      autoRefresh: false,
      indexedEvents: null,
      totalEvents: {},
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
      let percentage = this.indexedEvents / this.totalEvents.total
      return Math.floor(percentage * 100)
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
  },
  created() {
    this.timelineStatus = this.timeline.status[0].status
    if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
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
          this.indexedEvents = response.data.meta.lines_indexed
          console.log(response.data.objects)
          this.totalEvents = JSON.parse(response.data.objects[0].total_events)
          console.log(this.totalEvents)
          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
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
