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
  <div>
    <form v-on:submit.prevent="submitForm">
      <div class="field">
        <div class="file has-name">
          <label class="file-label">
            <input id="datafile" class="file-input" type="file" name="resume" v-on:change="setFileName($event.target.files)" />
            <span class="file-cta">
              <span class="file-icon">
                <i class="fas fa-upload"></i>
              </span>
              <span class="file-label">
                Choose a file…
              </span>
            </span>
            <span class="file-name" v-if="fileName">
              <span v-if="!fileName">Please select a file</span>
              {{ fileName }}
            </span>
          </label>
        </div>
      </div>
      <div class="field">
        <div v-if="error">
          <article class="message is-danger mb-0">
            <div class="message-body">
              {{ error }}
            </div>
          </article>
        </div>
      </div>

      <!-- 
      
      Next lines of code represent the dropdwon menu
      It is dynamically generated (with an extra option: New header) to allow
        the user to map the missing header with an exsting one

      -->
      <div v-for="(value, key) in headerMissing" :key="key">
        <label v-if="!value">{{key}} </label>
        <select v-if="!value" :name="key" :id="key" v-on:click="getSelection($event)">
          <option>New header</option>
          <option v-for="h in headers" :value="h" :key="h.id">
            <div v-if="!headerMissing[h.val]">
              {{h.val}}
            </div>
          </option>
        </select>
      </div>

      <div class="field" v-if="fileName">
        <label class="label">Name</label>
        <div class="control">
          <input v-model="form.name" class="input" type="text" required placeholder="Name your timeline" />
        </div>
        <div v-if="fileName.split('.')[1]==='csv'">
          <label class="label">CSV Separator</label>
          <div class="control" v-for="(v, key) in delimitersList" :key="key">
              <input type="radio" name="CSVDelimiter" :value="v" v-on:click="changeCSVDelimiter($event)" >
              {{key}} ({{v}})
          </div>
          <div v-if="infoMessage">
            <article class="message is-success mb-0">
              <div class="message-body">
                {{ infoMessage }}
              </div>
            </article>
          </div>
        </div>
      </div>
      <div class="error" v-if="!error">
        <div class="field" v-if="fileName && percentCompleted === 0">
          <div class="control">
            <input class="button is-success" type="submit" value="Upload" />
          </div>
        </div>
      </div>
    </form>
    <br />
    <b-progress
      v-if="percentCompleted !== 0"
      :value="percentCompleted"
      show-value
      format="percent"
      type="is-info"
      size="is-medium"
    >
      <span v-if="percentCompleted === 100">Waiting for request to finish..</span>
    </b-progress>
  </div>
</template>
<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      headersString : '', // headers string not formatted (used when changing CSV separator)
      headers: [], // headers in the CSV 
      headerMissing : {}, 
      headersMapping : {},
      form: {
        name: '',
        file: '',
      },
      fileName: '',
      error: '',
      percentCompleted: 0,
      CSVDelimiter: ',',
      infoMessage : '',
      delimitersList : {'Comma' : ',', 'Semicolon': ';', 'Pipe' : '|'}
    }
  },
  methods: {
    changeCSVDelimiter: function(e){
      this.CSVDelimiter = e.target.value;
      this.infoMessage = "CSV separator changed: < " + this.CSVDelimiter + " >."
      let headers = this.headersString.split(this.CSVDelimiter) // all  headers of CSV uploaded
      this.headers = []
      for(let i in headers){
        this.headers.push({
            id : i,
            val : headers[i]
        })
      }
      if( headers.indexOf("datetime") < 0 ){
          this.headerMissing["datetime"] = false;
          this.headersMapping["datetime"] = ["", ""]
      }else{
          delete this.headersMapping["datetime"]
          this.headerMissing["datetime"] = true;
      }
      if( headers.indexOf("message") < 0 ){
          this.headerMissing["message"] = false;
          this.headersMapping["message"] = ["", ""]
      }else{
        delete this.headersMapping["message"]
        this.headerMissing["message"] = true;
      }
      if( headers.indexOf("timestamp_desc") < 0 ){
        this.headersMapping["timestamp_desc"] = ["", ""]
        this.headerMissing["timestamp_desc"] = false;
      }else{
        delete this.headersMapping["timestamp_desc"]
        this.headerMissing["timestamp_desc"] = true;
      }
      let headerMissingArray = this.isHMissing()
      if (headerMissingArray.length > 0){
        this.error = 'Missing headers: ' + headerMissingArray.toString()
      }else{
        this.error = ''
      }
    },
    getSelection: function(e){
      /**
       * method to map of the missing headers
       * it verifies if some conditions are met before submitting the form,
       * in particular:
       * 1. missing headers must be map with exsiting headers in the CSV
       * 2. 2 or more missing headers can not be mapped to the same exsiting header
       * 3. If missing header can not be mapped with an existing one, then, 
       *      it can be "created" a new one and a default value is associated to each row for that header
       */

        var key = e.target.name; // key = datetime | message | timestamp_desc
        var value = e.target.options[e.target.options.selectedIndex].text; // value = existing CSV header
        this.headersMapping[key][0] = value
        if(value === "New header"){ // ask to the user the default row's value
          var newHeaderValue = ""
          while(!newHeaderValue){
            newHeaderValue = prompt("Insert the default value for this header")
            if(newHeaderValue.includes(this.CSVDelimiter)){
              alert("New header value cannot contain CSV separator")
              newHeaderValue = null
            }
          }
          this.headersMapping[key][1] = newHeaderValue
        }else{
          this.headersMapping[key][1] = ""
        }

        // get all the values of headersMapping and put them in array
        let allValues = []
        for(let k in this.headersMapping){
          allValues.push(this.headersMapping[k][0])
        }

        // 1. check if mapping is completed, i.e., if there are not empty or null field for the mapping
        if(!allValues.some(e => (e==='' || !e))){ 
          // 2. check if all selected headers are unique (except from 'New header')
          allValues = allValues.filter(e => e !== "New header")
          if(allValues.length === new Set(allValues).size){
            this.error = ""
          }else{
            // there are duplicates in the selection list
            this.error = "New headers mapping contains duplicates"  
          }
        }else{
          // meaning: Exist at least 1 element of allValues that is null or empty
          this.error = "Finish headers selection"
        }
    },
    clearFormData: function() {
      this.form.name = ''
      this.form.file = ''
      this.fileName = ''
      this.headersMapping = {
        "datetime" : [null, null],
        "message" : [null, null],
        "timestamp_desc" : [null, null],
      }
      this.headerMissing = {
        "datetime" : true,
        "message" : true,
        "timestamp_desc" : true,
      }
      this.infoMessage = ''
      this.headersString = ''
    },
    submitForm: function() {
      if (this.error === 'Please select a file with a valid extension' ) {
        return;
      }
      let formData = new FormData()
      formData.append('file', this.form.file)
      formData.append('name', this.form.name)
      formData.append('provider', 'WebUpload')
      formData.append('context', this.fileName)
      formData.append('total_file_size', this.form.file.size)
      formData.append('sketch_id', this.$store.state.sketch.id)
      let exstension = this.fileName.split('.')[1]
      if(exstension === 'csv'){
        var hMapping = JSON.stringify(this.headersMapping)
        formData.append('headersMapping', hMapping)
        formData.append('delimiter', this.CSVDelimiter)
      }
      let config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: function(progressEvent) {
          this.percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }.bind(this),
      }
      ApiClient.uploadTimeline(formData, config)
        .then(response => {
          this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
          this.$emit('toggleModal')
          this.clearFormData()
          this.percentCompleted = 0
       })
       .catch(e => {}) 
    },
    setFileName: function(fileList) {

      /* 1. Initilize the variables */

      // this mapping represents a dictionary where for each mandatory fields we assign
      // 0. name of the column to map
      // 1. value of the column in case we want to insert a new one
      //      e.g., we do not have timestamp_desc: we add a new one (the value of rows in this column
      //            will be the same)
      this.headersMapping = {
        "datetime" : [null, null],
        "message" : [null, null],
        "timestamp_desc" : [null, null],
      }
      // headers missing in the CSV:
      // if the headers is present, then the value of the corresponding field is set to true
      this.headerMissing = {
        "datetime" : true,
        "message" : true,
        "timestamp_desc" : true,
      }
      this.headersString = ''
      this.headers = []
      let fileName = fileList[0].name
      let fileExtension = fileName.split('.')[1]
      this.form.file = fileList[0]
      this.form.name = fileName
        .split('.')
        .slice(0, -1)
        .join('.')
      this.fileName = fileName
      this.error = ''
      this.infoMessage = ''
      
      /* 2. Check for the correct extension */
      let allowedExtensions = ['csv', 'json', 'jsonl', 'plaso']
      if (!allowedExtensions.includes(fileExtension)) {
        this.error = 'Please select a file with a valid extension'
      }

      // TODO: need to verify with JSONL files

      /* 3. Manage CSV missing headers */

      if(fileExtension === "csv"){
        var reader = new FileReader()
        var file = document.getElementById("datafile").files[0]
        
        // read only 1000 B --> it is reasonable that the header of the CSV file ends before the 1000^ byte.
        // this is done to prevent JS reading a large CSV file (GBs) 
        var vueJS = this
        reader.readAsText(file.slice(0, 1000))
        reader.onloadend = function(e){
            if (e.target.readyState === FileReader.DONE){  // DONE == 2
              
              /* 3a. Extract the headers from the CSV */ 
              
              var data = e.target.result
              vueJS.headersString = data.split("\n")[0]
              var headers = vueJS.headersString.split(vueJS.CSVDelimiter) // all  headers of CSV uploaded
              console.log(headers)
              for(let i in headers){
                vueJS.headers.push({
                    id : i,
                    val : headers[i]
                })
              }

              /* 3b. Check if the mandatory headers are present in the extracted ones */

              if( headers.indexOf("datetime") < 0 ){
                  vueJS.headerMissing["datetime"] = false;
              }else
                delete vueJS.headersMapping["datetime"]
              if( headers.indexOf("message") < 0 ){
                  vueJS.headerMissing["message"] = false;
              }else
                delete vueJS.headersMapping["message"]
              if( headers.indexOf("timestamp_desc") < 0 ){
                vueJS.headerMissing["timestamp_desc"] = false;
              }else
                delete vueJS.headersMapping["timestamp_desc"]
              
              let headerMissingArray = vueJS.isHMissing()
              if (headerMissingArray.length > 0){
                vueJS.error = 'Missing headers: ' + headerMissingArray.toString()
              }else{
                vueJS.error = ''
              }
            }
          }        
      }
    },
    isHMissing: function(){
      /**
       * isHMissing --> is there a missing header?
       * verify if there is at least one missing header
       * it returns an array containing the missing headers
       */
      let headerMissingArray = [] 
      for(let key in this.headerMissing){
        if(!this.headerMissing[key])
          headerMissingArray.push(key)
      }
      return headerMissingArray
    },
  },
}
</script>