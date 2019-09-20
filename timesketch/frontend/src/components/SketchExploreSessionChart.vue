<template>
    <div>
        <div v-if="this.spec === '{}' && this.showChart === true"><span class="icon"><i class="fas fa-circle-notch fa-pulse"></i></span> Loading..</div>
        <p v-if="isTruncated && showChart">Warning: only retrieved 100 sessions for each session type.</p>
        <ts-vega-lite-chart :vegaSpec="spec" @viewCreated="registerClickListener"></ts-vega-lite-chart>
        <div class="field">
            <button class="button" @click="toggleChart" :disabled="indices.length > 1">{{message}}</button>
        </div>

        <div class="field" v-if="showChart">
            <p v-if="!this.showTimeRange">
                Showing sessions within the last year of the timeline by default. <u><em @click="toggleTimeRange">Choose a different timeframe.</em></u>
            </p>
            <div v-if="this.showTimeRange" class="control">
                <label class="label"><em>Start date:</em></label>
                <input class="input" type="text" name="start_time_range_input" placeholder="mm/dd/yyyy" @change="updateTimeRange">
                <label class="label"><em>End date:</em></label>
                <input class="input" type="text" name="end_time_range_input" placeholder="mm/dd/yyyy" @change="updateTimeRange">
            </div>
            <p>{{timeRangeMessage}}</p>
        </div>

        <div class="field" v-if="showChart">
            <label class="label">Type of Session:</label>
            <div class="control">
                <div class="select">
                    <select v-model="selectedType" @change="selectSessionType">
                        <option disabled value="">Please select one</option>
                        <option v-for="session_type in sessionTypes" :value=session_type v-bind:key="session_type">{{session_type}}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="field" v-if="selectedSessions.length > 0"> 
            <label class="label">Session ID:</label>
            <div class="control">
                <div class="select">
                    <select v-model="selectedID" @change="selectSessionID">
                        <option disabled value="">Please select one</option>
                        <option v-for="session in selectedSessions" :value=session.session_id v-bind:key="session.session_type + session.session_id">{{session.session_id}}</option>
                    </select>
                </div>
            </div>
        </div>
   </div>
</template>

<script>
import TsVegaLiteChart from './VegaLiteChart'
import ApiClient from '../utils/RestApiClient'

export default {
  name: 'ts-explore-session-chart',
  components: {
        TsVegaLiteChart
  },

  data () {
      return {
            processedSessions: [],
            message: 'Show Session Chart',
            showChart: false,
            showTimeRange: false,
            selectedSessions: [],
            spec: '{}',
            sessionTypes: ['all'],
            barSize: 0,
            smallest_timestamp: 0,
            selectedType: '',
            selectedID: '',
            sessions: [],
            startTimeRange: null,
            endTimeRange: null,
            timeRangeMessage: '',
            isTruncated: false
      }
  },

  computed: {
    sketch () {
        return this.$store.state.sketch
    },
    indices () {
        return this.$store.state.currentQueryFilter.indices
    }
  },

  methods: {
    registerClickListener: function (view) {
        var store = this.$store
        var sketchId = this.sketch.id
        view.addEventListener('click', function (event, item) {
            var session_type = item.datum.session_type
            var session_id = item.datum.session_id
            if (session_type != undefined && session_id != undefined) {
                var queryString = 'session_id.' + session_type + ':' + session_id
                store.commit('updateCurrentQueryString', queryString)
                store.commit('search', sketchId)
            }
        })
    },

    toggleChart: function () {
        this.showChart = !this.showChart
        if (this.showChart) {
            this.message = 'Hide Session Chart'
            if (this.sessions.length == 0) {
                ApiClient.getSessions(this.sketch.id, this.indices[0]).then((response) => {
                    this.sessions = response.data
                    this.sessionTypes = this.sessionTypes.concat([...new Set(this.sessions.map(s => s.session_type))])
                    this.getVegaSpec()
                }).catch((e) => {})
            }
            else {
                this.getVegaSpec()
            }
        }
        else {
            this.message = 'Show Session Chart'
            this.selectedSessions = []
            this.spec = '{}'
            this.selectedType = ''
            this.selectedID = ''
            this.showTimeRange = false
            this.startTimeRange  = Date.now() - 31556952000,
            this.endTimeRange = Date.now(),
            this.timeRangeMessage = ''
        }
    },

    toggleTimeRange: function () {
        this.showTimeRange = !this.showTimeRange
    },
    
    updateTimeRange: function (event) {
        const DATE_REGEX = /\d{1,2}\/\d{1,2}\/\d{4}/
        if(DATE_REGEX.test(event.target.value)) {
            this.timeRangeMessage = ''
            this.selectedSessions = []
            this.selectedType = ''
            this.selectedID = ''
            if (event.target.name === "start_time_range_input") {
                this.startTimeRange = new Date(event.target.value).getTime()
            }
            else {
                this.endTimeRange = new Date(event.target.value).getTime()
            }
            this.getVegaSpec()
        }
        else {
            this.timeRangeMessage = 'Please enter a valid date.'
        }
    },

    selectSessionType: function (event) {
        this.selectedID = ''
        var dictSpec = JSON.parse(this.spec)
        if (this.selectedType === 'all') {
            this.selectedSessions = []
            dictSpec['data']['values'] = this.processedSessions
        }
        else {
            this.selectedSessions = this.processedSessions.filter(session => session['session_type'] === this.selectedType)
            dictSpec['data']['values'] = this.selectedSessions
        }
        dictSpec['vconcat'][1]['selection']['brush']['init']['x'] = [this.smallest_timestamp, this.smallest_timestamp + (this.barSize * 50)]
        this.spec = JSON.stringify(dictSpec)
    },

    selectSessionID: function (event) {
        var queryString = ''
        var selection = []

        var selectedSessionsCopy = JSON.parse(JSON.stringify(this.selectedSessions))
        for (var i = 0; i < selectedSessionsCopy.length; i++) {
            var session = selectedSessionsCopy[i]
            if (this.selectedType === session.session_type && this.selectedID === session.session_id) {
                session['selected'] = true
                queryString = 'session_id.' + session['session_type'] + ':' + session['session_id']
                selection = [session['start_timestamp'] - (this.barSize * 5), session['end_timestamp'] + (this.barSize * 5)]
            }
            else {
                session['selected'] = false
            }
        }

        var dictSpec = JSON.parse(this.spec)
        dictSpec['data']['values'] = selectedSessionsCopy
        dictSpec['vconcat'][1]['selection']['brush']['init']['x'] = selection
        this.spec = JSON.stringify(dictSpec)

        this.$store.commit('updateCurrentQueryString', queryString)
        this.$store.commit('search', this.sketch.id)
    },

    getProcessedSessions: function () {
        //increases the visibility of sessions when plotted
        const YEAR_IN_MS = 31556952000

        var processedSessions = JSON.parse(JSON.stringify(this.sessions))
        this.isTruncated = processedSessions.pop()['truncated']

        if (processedSessions.length > 0) {
            var largest_timestamp = processedSessions[0].end_timestamp
            var smallest_timestamp = processedSessions[0].start_timestamp

            if (this.endTimeRange == null) {
                for (var i = 1; i < processedSessions.length; i++) {
                    if (processedSessions[i].end_timestamp > largest_timestamp) {
                        largest_timestamp = processedSessions[i].end_timestamp
                    }
                }
                this.endTimeRange = largest_timestamp
                this.startTimeRange = this.endTimeRange - YEAR_IN_MS
                processedSessions = processedSessions.filter(session => session.start_timestamp >= this.startTimeRange && session.start_timestamp <= this.endTimeRange)

                smallest_timestamp = processedSessions[0].start_timestamp
                for (var i = 1; i < processedSessions.length; i++) {
                    if (processedSessions[i].start_timestamp < smallest_timestamp) {
                        smallest_timestamp = processedSessions[i].start_timestamp
                    }
                }
            }

            else {
                processedSessions = processedSessions.filter(session => session.start_timestamp >= this.startTimeRange && session.start_timestamp <= this.endTimeRange)

                smallest_timestamp = processedSessions[0].start_timestamp
                largest_timestamp = processedSessions[0].end_timestamp
                for (var i = 1; i < processedSessions.length; i++) {
                    if (processedSessions[i].start_timestamp < smallest_timestamp) {
                        smallest_timestamp = processedSessions[i].start_timestamp
                    }
                    if (processedSessions[i].end_timestamp > largest_timestamp) {
                        largest_timestamp = processedSessions[i].end_timestamp
                    }
                }
            }
            
            var timeRange = (largest_timestamp - smallest_timestamp)

            //session bars will take up 1/1000th of the chart if they would otherwise be smaller
            this.barSize = Math.round(timeRange / 1000)
            this.smallest_timestamp = smallest_timestamp

            for (var i = 0; i < processedSessions.length; i++) {
                var session = processedSessions[i]
                var extended_end = session.start_timestamp + this.barSize
                if (session.end_timestamp < extended_end) {
                    session.end_timestamp = extended_end
                }
            }
        }
        this.processedSessions = processedSessions
    },

    getVegaSpec: function () {
        //TODO: make the size of the chart responsive
        const WIDTH = 900
        const HEIGHT = 400

        this.getProcessedSessions()
        if (this.processedSessions === undefined || this.processedSessions.length == 0) {
            this.timeRangeMessage = 'There are no sessions in this time range.'
        }

        var dictSpec = { "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "data": {
                "values": this.processedSessions
            },
            "vconcat": [{
                "width": WIDTH,
                "height": HEIGHT,
                "padding": 5,

                "mark": "bar",

                "encoding": {
                    "y": {"field": "session_type", "type": "ordinal", "axis": {"title": "Session Type"}},
                    "x": {"field": "start_timestamp", "type": "temporal",  "timeUnit": "yearmonthdatehoursminutesseconds", "axis": {"title": "Timestamp", "tickCount": 5}, "scale": {"domain": {"selection": "brush"}}},
                    "x2": {"field":"end_timestamp", "type": "temporal",  "timeUnit": "yearmonthdatehoursminutesseconds", "axis": {"title": "End Timestamp"}},
                    "color": {
                        "field": "session_id", "type": "nominal",
                        "scale": {"scheme": "tableau20"},
                        "legend": false
                    },
                    "opacity": {
                        "condition": [
                            {"test":"datum.selected == true", "value": 1}, 
                            {"test":"datum.selected == false", "value": 0.2}
                        ],
                        "value": 0.8
                    }
                }
            }, {
                "width": WIDTH,
                "height": HEIGHT / 4,
                "padding": 5,

                "selection": {
                    "brush": {
                        "type": "interval",
                        "encodings": ["x"],
                        "init": {"x": [this.smallest_timestamp, this.smallest_timestamp + (this.barSize * 50)]}
                    }
                },

                "mark": {"type": "bar", "x2Offset": WIDTH / 100, "clip": true},

                "encoding": {
                    "y": {"field": "session_type", "type": "ordinal", "axis": {"title": "Session Type"}},
                    "x": {"field": "start_timestamp", "type": "temporal", "axis": {"title": "Timestamp", "tickCount": 5}},
                    "x2": {"field": "end_timestamp", "type": "temporal", "axis": {"title": "End Timestamp"}},
                    "color": {
                        "field": "session_id", "type": "nominal",
                        "scale": {"scheme": "tableau20"},
                        "legend": false
                    },
                    "opacity": {
                        "condition": [
                            {"test":"datum.selected == true", "value": 1}, 
                            {"test":"datum.selected == false", "value": 0.2}
                        ],
                        "value": 0.8
                    }
                }
            }]
        }
        this.spec = JSON.stringify(dictSpec)
    }
  }
}
</script>

<style lang="scss"></style>