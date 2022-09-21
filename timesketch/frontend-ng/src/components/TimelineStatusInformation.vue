<template>
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
        <li v-if="timelineStatus === 'processing'"><strong>Percentage Completed</strong> {{ percentage }} %</li>
        <li v-if="timelineStatus === 'processing'"><strong>Remaining time:</strong> {{ remainingTime }}</li>
      </ul>

      <br /><br />
      <v-alert
        v-for="datasource in datasources"
        :key="datasource.id"
        colored-border
        border="left"
        elevation="1"
        :type="datasourceStatusColors(datasource)"
      >
        <ul style="list-style-type: none">
          <li><strong>Total File Events:</strong>{{ totalEventsDatasource(datasource.original_filename) }}</li>
          <li v-if="datasource.status === 'fail'">
            <strong>Error message:</strong>
            <code v-if="datasource.error_message"> {{ datasource.error_message }}</code>
          </li>

          <li><strong>Provider:</strong> {{ datasource.provider }}</li>
          <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
          <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
          <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
          <li><strong>Data label:</strong> {{ datasource.data_label }}</li>
          <li><strong>Status:</strong> {{ datasource.status }}</li>
        </ul>
        <br />
      </v-alert>
      <v-progress-linear
        v-if="timelineStatus === 'processing'"
        color="light-blue"
        height="10"
        :value="percentage"
        striped
      ></v-progress-linear>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn color="primary" text @click="$emit('closeDialog')"> Close </v-btn>
    </v-card-actions>
  </v-card>
</template>
<script>
export default {
  props: ['timeline', 'indexedEvents', 'totalEvents', 'timelineStatus', 'datasources', 'percentage', 'remainingTime'],
  data() {
    return {}
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    datasourceStatusColors(datasource) {
      if (datasource.status === 'ready' || datasource.status === null) {
        return 'info'
      } else if (datasource.status === 'processing') {
        return 'warning'
      }
      // status = fail
      return 'error'
    },
    totalEventsDatasource(originalFilename) {
      if (this.totalEvents) {
        return this.totalEvents.find((x) => x.originalFilename === originalFilename).totalFileEvents
      } else {
        return this.timeline.datasources.find((x) => x.original_filename === originalFilename).total_file_events
      }
    },
  },
}
</script>
