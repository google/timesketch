<template>
  <v-dialog v-model="dialog" width="600">
    <template v-slot:activator="{ on, attrs }">
      <small v-bind="attrs" v-on="on">
        <v-icon v-if="timelineStatus === 'ready'">mdi-check-circle</v-icon>
        <v-icon v-if="timelineStatus === 'processing'">mdi-circle-slice-7</v-icon>
        <v-icon v-if="timelineStatus === 'fail'">mdi-alert-circle</v-icon>
      </small>
    </template>
    <v-card>
      <v-app-bar flat dense>Detailed information for: {{ timeline.name }}</v-app-bar>
      <v-card-text class="pa-5">
        <ul style="list-style-type: none">
          <li><strong>Opensearch index: </strong>{{ timeline.searchindex.index_name }}</li>
          <li v-if="timelineStatus === 'processing' || timelineStatus === 'ready'">
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
            <li v-if="timelineStatus === 'processing' || timelineStatus === 'ready'">
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

            <li v-if="timelineStatus === 'fail'">
              <strong>Error message:</strong>
              <code v-if="datasource.error_message"> {{ datasource.error_message }}</code>
            </li>

            <li v-if="timelineStatus !== 'processing'"><strong>Provider:</strong> {{ datasource.provider }}</li>
            <li v-if="timelineStatus !== 'processing'"><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
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
</template>
<script>
export default {
  props: ['timeline', 'indexedEvents', 'totalEvents', 'timelineStatus'],
  data() {
    return {
      dialog: false,
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
      let percentage = Math.min(Math.floor((this.indexedEvents / totalEvents) * 100), 100)
      if (this.timelineStatus === 'ready') percentage = 100
      return percentage
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
  methods: {
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
}
</script>
