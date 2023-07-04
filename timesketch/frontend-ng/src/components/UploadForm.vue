<!--
Copyright 2019 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <span>
    <v-dialog v-model="percentageFlag" persistent width="700">
      <v-card flat class="pa-5">
        Uploading..
        <br /><br />
        <v-progress-linear color="light-blue" height="25" :value="percentCompleted"
          >{{ percentCompleted }}%</v-progress-linear
        >
        <v-divider></v-divider>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialog" max-width="1000">
      <template v-slot:activator="{ on, attrs }">
        <v-btn v-if="btnType === 'small'" small text rounded color="primary" v-bind="attrs" v-on="on">
          <v-icon left small> mdi-plus </v-icon>
          Add Timeline
        </v-btn>
        <v-btn v-else outlined color="primary" v-bind="attrs" v-on="on">
          <v-icon left> mdi-plus </v-icon>
          Add Timeline
        </v-btn>
      </template>
      <v-card>
        <v-container class="pa-4">
          <h3>{{ title }}</h3>
          <br />

          <div v-if="error.length > 0">
            <v-alert outlined type="error" v-for="(errorMessage, index) in error" :key="index">
              {{ errorMessage }}
              <br /><br />
              <div v-if="['csv', 'jsonl', 'json'].includes(extension)">
                <v-simple-table v-if="headers.length > 0">
                  <template v-slot:default>
                    <thead>
                      <tr>
                        <th
                          v-for="mandatoryHeader in headersTable"
                          :key="mandatoryHeader.name"
                          :style="mandatoryHeader.color"
                          class="text-left"
                        >
                          <div v-if="missingHeaders.includes(mandatoryHeader.name)">
                            <v-select
                              :items="listHeadersSelectMenu"
                              :label="mandatoryHeader.name"
                              v-model="mandatoryHeaders.find((h) => h.name === mandatoryHeader.name).columnsSelected"
                              multiple
                              chips
                              hint="Mapped to"
                              persistent-hint
                              @change="changeHeaderMapping($event, mandatoryHeader.name)"
                            ></v-select>
                          </div>
                          <div v-else>
                            <span class="tag is-large" :style="mandatoryHeader.color">
                              <label>{{ mandatoryHeader.name }}</label>
                            </span>
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <br />
                    <strong>Preview</strong>
                    <tbody>
                      <tr v-for="i in numberRows" :key="i">
                        <td v-for="mandatoryHeader in headersTable" :key="mandatoryHeader.name">
                          {{ mandatoryHeader.values[i - 1] }}
                        </td>
                      </tr>
                    </tbody>
                  </template>
                </v-simple-table>
              </div>
            </v-alert>
          </div>

          <div v-if="fileName">
            <v-text-field label="Timeline Name" outlined v-model="form.name"></v-text-field>
            <v-radio-group v-if="extension === 'csv'" v-model="CSVDelimiter">
              <template v-slot:label>
                <div>Choose <strong>CSV delimiter</strong></div>
              </template>
              <v-radio v-for="(v, key) in delimitersList" :value="v" @change="changeCSVDelimiter(v)" :key="key">
                <template v-slot:label>
                  <div>{{ key }} ({{ v }})</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-list v-if="!percentageFlag">
              File info
              <v-simple-table height="100px">
                <template v-slot:default>
                  <thead>
                    <tr>
                      <th v-for="(value, key) in fileMetaData" :key="key" class="text-left">
                        {{ key }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td v-for="(value, key) in fileMetaData" :key="key" class="text-left">
                        {{ value }}
                      </td>
                    </tr>
                  </tbody>
                </template>
              </v-simple-table>
            </v-list>
          </div>

          <div v-else>
            <v-file-input
              label="Select file (Plaso/JSONL/CSV)"
              outlined
              dense
              clearable
              multiple
              show-size
              truncate-length="15"
              id="datafile"
              v-model="uploadedFiles"
              @change="setFile($event)"
              @click:clear="clearFormData"
            ></v-file-input>
          </div>
        </v-container>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog = false"> Cancel </v-btn>
          <v-btn v-if="fileName" text @click="clearFormData()"> Select another file </v-btn>
          <v-btn color="primary" text @click="submitForm()" v-if="!(error.length > 0 || !fileName)"> Submit </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </span>
</template>
<script>
import ApiClient from '../utils/RestApiClient'

export default {
  props: ['btnType'],
  data() {
    return {
      headersString: '', // headers string not formatted (used when changing CSV separator)
      valuesString: [],
      title: 'Upload Plaso/JSONL/CSV file',
      /**
       *  headersMapping: list of object containing the:
       * (i) target header to be modified [key=target],
       * (ii) the source header to be substituted [key=source] and
       * (iii) the default value in case we add a new columns [key=default_value].
       */
      headersMapping: [],
      mandatoryHeaders: [
        { name: 'datetime', columnsSelected: [] },
        { name: 'message', columnsSelected: [] },
      ],
      form: {
        name: '',
        file: '',
      },
      fileName: '',
      fileMetaData: {},
      error: [],
      percentCompleted: 0,
      uploadedFiles: [],

      CSVDelimiter: ',',
      infoMessage: '',
      delimitersList: { Comma: ',', Semicolon: ';', Pipe: '|' },
      showHelperFlag: false,
      showPreviewFlag: false,
      showAddColumnFlag: false,
      checkedHeaders: [],
      staticNumberRows: 3,
      dialog: false,
      colors: [
        { name: 'red', value: 'background-color: #FEECF0; color:#CC0F35' },
        { name: 'blue', value: 'background-color: #EEF6FC; color:#1D72AA' },
        { name: 'green', value: 'background-color: #EFFAF3; color:#257942' },
      ],
    }
  },
  computed: {
    headers() {
      let headers = []
      if (this.extension === 'csv') {
        headers = this.headersString.split(this.CSVDelimiter)
      } else if (['json', 'jsonl'].includes(this.extension)) {
        headers = Object.keys(this.headersString)
      }
      return headers
    },
    missingHeaders() {
      return this.mandatoryHeaders.filter((header) => this.headers.indexOf(header.name) < 0).map((h) => h.name)
    },
    listHeadersSelectMenu() {
      let mandatoryHeaders = new Set(this.mandatoryHeaders.map((h) => h.name))
      let headers = this.headers.filter((h) => !mandatoryHeaders.has(h))
      headers.unshift('Create New Header')
      return headers
    },
    extension() {
      let extension = this.fileName.split('.')
      if (extension.length > 1) return extension[extension.length - 1].toLowerCase()
      else return null
    },
    numberRows() {
      if (this.extension === 'csv') {
        let n = this.valuesString.indexOf('')
        return n < 0 ? this.staticNumberRows : n
      } else if (['json', 'jsonl'].includes(this.extension)) {
        return this.valuesString.length
      } else {
        return 0
      }
    },
    percentageFlag() {
      return this.percentCompleted > 0
    },
    sketch() {
      return this.$store.state.sketch
    },
    headersTable() {
      /**
       * headersTable = [
       *                    {name : "datetime", values : ["v1", "v2", "v3"]},
       *                    {name : "message", values : ["v1", "v2", "v3"]},
       *                    {name : "timestamp_desc", values : ["v1", "v2", "v3"]},
       *                 ]
       */

      /**
       * valuesAndHeaders = dictionary where
       *  - the key is the header, e.g., "datetime", "file_name"
       *  - the value is an array containing the values of that column
       */
      let valuesAndHeaders = {}
      if (this.extension === 'csv') {
        let values = this.valuesString.map((x) => x.split(this.CSVDelimiter))
        /**
         * values is an array of array (matrix)
         * For example, for a CSV with 3 headers such as datetime, timestamp description and permission
         * E.g., values = | [2022-11-10, file_delete, high] |
         *                | [2022-11-09, file_create, high] |
         *                | [2022-11-09, file_update, low]  |
         */
        for (let i = 0; i < this.headers.length; i++) {
          let listValues = []
          for (let j = 0; j < values.length; j++) {
            listValues.push(values[j][i]) // list values aggregate the information on the columns
          }
          valuesAndHeaders[this.headers[i]] = listValues
        }
      } else if (['json', 'jsonl'].includes(this.extension)) {
        for (let i = 0; i < this.valuesString.length; i++) {
          for (let header in this.valuesString[i]) {
            if (header in valuesAndHeaders) {
              valuesAndHeaders[header].push(this.valuesString[i][header])
            } else {
              valuesAndHeaders[header] = [this.valuesString[i][header]]
            }
          }
        }
      } else {
        console.error(this.extension + ' file extension not supported for this feature')
      }
      let checkedHeaders = this.checkedHeaders
      return checkedHeaders.sort().map((header) => {
        let color = '' // CSS property for the displayed column
        let values = [] // values that we will display for the checked header

        if (this.headers.includes(header)) {
          // case 0: the mandatory header is in the CSV (no mapping required)
          values = valuesAndHeaders[header]
          color = this.colors.find((x) => x.name === 'blue').value
        } else {
          // header is missing, need to check to headers mapping
          // case 1: we map the header with only one column -> rename column
          // case 2: we map the header with multiple fields -> combine columns
          // case 3: we want to create a new column with a default value -> create a new column
          // case 4: we haven't mapped the header yet

          // extract from the headersMapping the user's choice (it may be null if the user has not mapped the header yet)
          let extractedMapping = this.headersMapping.find((x) => x.target === header)
          if (extractedMapping) {
            if (extractedMapping.source) {
              if (extractedMapping.source.length === 1) {
                // case 1
                values = valuesAndHeaders[extractedMapping.source[0]]
              } else {
                // case 2
                let listSources = extractedMapping.source
                for (let i = 0; i < this.numberRows; i++) {
                  let concatValue = ''
                  listSources.forEach((source) => {
                    concatValue += source + ': '
                    concatValue += JSON.stringify(valuesAndHeaders[source][i]) + ' | '
                  })
                  values.push(concatValue)
                }
              }
            } else {
              // case 3
              values = Array(this.numberRows).fill(extractedMapping.default_value)
            }
            color = this.colors.find((x) => x.name === 'green').value
          } else {
            // case 4
            values = Array(this.numberRows).fill('Header not mapped')
            color = this.colors.find((x) => x.name === 'red').value
          }
        }
        return { name: header, values: values, color: color }
      })
    },
  },
  methods: {
    showHelper() {
      // first hide the other menus
      this.showPreviewFlag = false
      this.showAddColumnFlag = false

      this.showHelperFlag = !this.showHelperFlag
    },
    showPreview() {
      this.showHelperFlag = false
      this.showPreviewFlag = !this.showPreviewFlag
      if (!this.showPreviewFlag) this.showAddColumnFlag = false
    },
    showAddColumn() {
      this.showAddColumnFlag = !this.showAddColumnFlag
    },
    getDefaultValue: function (target) {
      let obj = this.headersMapping.find((x) => x['target'] === target)
      if (obj) {
        return obj['default_value']
      } else {
        return null
      }
    },
    changeCSVDelimiter: function (value) {
      this.CSVDelimiter = value
      for (let i = 0; i < this.mandatoryHeaders.length; i++) {
        this.mandatoryHeaders[i]['columnsSelected'] = []
      }
      this.headersMapping = []
      this.validateFile()
    },
    changeHeaderMapping: function (columnsSelected, target) {
      /**
       * Method to map the missing headers.
       * First, it checks some conditions, in particular, the user needs to:
       * 1. map the missing header with any existing one in the CSV,
       * 2. avoid to map 2 or more missing headers with the same exsiting one,
       * 3. specify a default value in case he chooses to create a new column
       */
      let lastElementSelected = columnsSelected[columnsSelected.length - 1]
      let i = this.mandatoryHeaders.findIndex((h) => h.name === target)
      if (lastElementSelected === 'Create New Header') {
        this.mandatoryHeaders[i].columnsSelected = ['Create New Header']
      } else {
        this.mandatoryHeaders[i].columnsSelected = this.mandatoryHeaders[i].columnsSelected.filter(
          (h) => h !== 'Create New Header'
        )
      }
      let sources = []
      let defaultValue = null
      if (lastElementSelected === 'Create New Header') {
        sources = null
        do {
          defaultValue = prompt('Insert the default value for this header')
          if (defaultValue.includes(this.CSVDelimiter)) {
            alert(`New header value cannot contain CSV separator (found ${this.CSVDelimiter})`)
            defaultValue = null
          }
        } while (!defaultValue)
      } else {
        sources = this.mandatoryHeaders[i].columnsSelected
      }

      this.headersMapping = this.headersMapping.filter((mapping) => mapping['target'] !== target)
      if (sources === null || sources.length > 0)
        this.headersMapping.push({
          target: target,
          source: sources,
          default_value: defaultValue,
        })
      this.validateFile()
    },
    clearFormData: function () {
      this.fileMetaData = {}
      this.form.name = ''
      this.form.file = ''
      this.fileName = ''
      this.headersMapping = []
      this.infoMessage = ''
      this.headersString = ''
      this.valuesString = []
      this.uploadedFiles = []
      this.title = 'Upload Plaso/JSONL/CSV file'
      this.error = []
      this.percentCompleted = 0

      for (let i = 0; i < this.mandatoryHeaders.length; i++) {
        this.mandatoryHeaders[i]['columnsSelected'] = []
      }
    },
    submitForm: function () {
      if (!this.validateFile()) {
        return
      }

      let formData = new FormData()
      formData.append('file', this.form.file)
      formData.append('name', this.form.name)
      formData.append('provider', 'WebUpload')
      formData.append('context', this.fileName)
      formData.append('total_file_size', this.form.file.size)
      formData.append('sketch_id', this.sketch.id)
      if (['csv', 'jsonl', 'json'].includes(this.extension)) {
        let hMapping = JSON.stringify(this.headersMapping)
        formData.append('headersMapping', hMapping)
        formData.append('delimiter', this.CSVDelimiter)
      }
      let config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: function (progressEvent) {
          this.percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }.bind(this),
      }
      this.dialog = false
      ApiClient.uploadTimeline(formData, config)
        .then(() => {
          this.clearFormData()
          this.percentCompleted = 0
          this.$store.dispatch('updateSketch', this.sketch.id)
        })
        .catch((e) => {})
    },
    validateFile: function () {
      this.error = []
      if (this.form.file.size <= 0) {
        this.error.push('Please select a non empty file')
      }
      let allowedExtensions = ['csv', 'json', 'jsonl', 'plaso']
      if (!allowedExtensions.includes(this.extension)) {
        this.error.push('Please select a file with a valid extension: ' + allowedExtensions.toString())
      }
      if (['csv', 'jsonl', 'json'].includes(this.extension)) {
        // 1. check if mapping is completed, i.e., if the user set all the mandatory headers
        if (this.headersMapping.length !== this.missingHeaders.length) {
          this.error.push('Missing headers: ' + this.missingHeaders.toString())
        }
        // 2. check for duplicate headers (except from the new header and multiple headers)
        let duplicates = this.headersMapping.filter((mapping) => mapping['source']).map((e) => e.source)
        duplicates = duplicates.filter((x) => x.length === 1).map((x) => x[0]) // only mapping 1:1. They will be renamed on the database thus we do not want duplicates
        if (duplicates.length > new Set(duplicates).size) {
          this.error.push(`New headers mapping contains duplicates (${duplicates})`)
        }
      }
      if (this.error.length === 0) {
        this.title = 'Select file to upload'
      } else {
        this.title = 'Almost there... Map the ' + this.missingHeaders.length + ' missing headers.'
      }
      return this.error.length === 0
    },
    setFile: function (fileList) {
      /* 1. Initilize the variables */

      if (!fileList[0]) {
        return
      }
      const bytesToMegaBytes = (bytes) => bytes / 1024 ** 2
      this.fileMetaData = {
        Name: fileList[0].name,
        Size: bytesToMegaBytes(fileList[0].size) + ' MB',
      }
      let fileName = fileList[0].name
      this.headersMapping = []
      this.headersString = ''
      this.valuesString = []
      this.form.file = fileList[0]
      this.form.name = fileName.split('.').slice(0, -1).join('.')
      this.fileName = fileName
      /* 3. Manage CSV missing headers */
      if (this.extension === 'csv') {
        this.extractCSVHeader()
      } else if (['json', 'jsonl'].includes(this.extension)) {
        this.extractJSONLHeader()
      } else {
        this.validateFile()
      }
      this.checkedHeaders = this.mandatoryHeaders.map((x) => x.name)
    },
    extractCSVHeader: function () {
      let reader = new FileReader()
      let file = document.getElementById('datafile').files[0]

      // read only 1000 B --> it is reasonable that the header of the CSV file ends before the 1000^ byte.
      // Done to prevent JS reading a large CSV file (GBs)
      let vueJS = this
      reader.readAsText(file.slice(0, 10000))
      reader.onloadend = function (e) {
        if (e.target.readyState === FileReader.DONE) {
          /* 3a. Extract the headers from the CSV */
          let data = e.target.result
          vueJS.headersString = data.split('\n')[0].replaceAll('"', '')
          vueJS.valuesString = data.split('\n').slice(1, vueJS.staticNumberRows + 1)
          vueJS.validateFile()
        }
      }
    },
    extractJSONLHeader: function () {
      let reader = new FileReader()
      let file = document.getElementById('datafile').files[0]
      let vueJS = this
      reader.readAsText(file.slice(0, 10000))
      reader.onloadend = function (e) {
        if (e.target.readyState === FileReader.DONE) {
          /* 3a. Extract the headers from the CSV */
          let data = e.target.result
          let rows = data.split('\n').filter((jsonlLine) => jsonlLine !== '')
          let i = Math.min(vueJS.staticNumberRows, rows.length)
          try {
            vueJS.headersString = JSON.parse(rows[0])
            vueJS.valuesString = rows.slice(0, i).map((x) => JSON.parse(x))
            vueJS.validateFile()
          } catch (objError) {
            let error = objError.message
            error += '. Your first lines of JSON: '
            error += rows[0]
            error += '. Be sure to upload a JSON file in a JSONL format.'
            vueJS.title = 'Cannot parse the JSON file'
            vueJS.error.push(error)
          }
        }
      }
    },
  },
}
</script>
