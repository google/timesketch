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
            <input
              id="datafile"
              class="file-input"
              type="file"
              name="resume"
              @change="setFile($event.target.files)"
            />
            <span class="file-cta">
              <span class="file-icon">
                <i class="fas fa-upload"></i>
              </span>
              <span class="file-label"> Choose a file… </span>
            </span>
            <span class="file-name" v-if="fileName">
              <span v-if="!fileName">Please select a file</span>
              {{ fileName }}
            </span>
          </label>
        </div>
      </div>

      <div class="field">
        <div v-if="['json', 'jsonl', 'csv'].includes(extension) && valuesString !== ''">
          <hr />

          <!-- List of button: showHelper, showPreview, addColumnsToPreview -->
          <button type="button" class="button is-success" @click="showHelper">
            {{ showHelperFlag ? "Hide Helper" : "Show Helper" }}</button
          >&emsp;
          <button type="button" class="button is-success" @click="showPreview">
            {{ showPreviewFlag ? "Hide preview" : "Show preview" }}</button
          >&emsp;
          <button
            v-if="showPreviewFlag"
            type="button"
            class="button is-success"
            @click="showAddColumn"
          >
            {{ showAddColumnFlag ? "Hide columns" : "Add Columns" }}</button
          ><br /><br />

          <!-- Dynamically generation of the preview of the CSV file -->
          <div v-if="showPreviewFlag">
            <span>
              <article class="message is-info mb-0">
                <div class="message-body">
                  The columns shown in the preview are only a representation of
                  what will be uploaded on the server. Adding or removing
                  columns using the "Add columns" button does not affect what
                  will be uploaded on the server.
                </div>
              </article>
            </span>
            <ul
              v-if="showAddColumnFlag"
              style="
                list-style: none;
                height: 100px;
                width: 100%;
                overflow: auto;
              "
            >
              <li v-for="header in allHeaders" :key="header">
                <input
                  type="checkbox"
                  :value="header"
                  v-model="checkedHeaders"
                />
                {{ header }}
              </li>
            </ul>
            <br />
            <table id="example" class="table is-striped" style="width: 100%">
              <thead>
                <tr>
                  <th
                    v-for="mandatoryHeader in headersTable"
                    :key="mandatoryHeader.name"
                    :style="mandatoryHeader.color"
                  >
                    {{ mandatoryHeader.name }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="i in numberRows" :key="i">
                  <td
                    v-for="mandatoryHeader in headersTable"
                    :key="mandatoryHeader.name"
                  >
                    {{ mandatoryHeader.values[i - 1] }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Helper menu -->
          <div v-if="showHelperFlag">
            <header class="modal-card-head">
              <p class="modal-card-title">Header Mapping Helper</p>
            </header>
            <section class="modal-card-body">
              <div>
                The form below allows you to map the headers in your file to the
                mandatory ones:
                <div class="content">
                  <ul>
                    <li v-for="header in missingHeaders" :key="header.name">
                      {{ header.name }}
                    </li>
                  </ul>
                </div>
                You can map a missing header using a dropdown menu or a list of
                checkboxes.
                <div class="content">
                  <ul>
                    <li>
                      Dropdown menu:
                      <div class="content">
                        <ul>
                          <li>
                            Choose one existing header from your CSV. Timesketch
                            will rename that column with the name of the missing
                            header.
                          </li>
                          <li>
                            Create a new column by selecting "Create new
                            header". Timesketch will add a new column with the
                            name of the missing header. Doing so, you need to
                            specify a default value that Timesketch will use to
                            fill the new column.
                          </li>
                        </ul>
                      </div>
                    </li>
                    <li>
                      List of checkboxes:
                      <div class="content">
                        <ul>
                          <li>
                            By choosing only one checkbox, Timesketch will
                            rename that column with the name of the missing
                            header.
                          </li>
                          <li>
                            By choosing more than one checkbox, Timesketch will
                            create a new column that combines the different
                            values of the selected columns.
                          </li>
                        </ul>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </section>
          </div>
          <hr
            style="
              height: 2px;
              border-width: 0;
              color: gray;
              background-color: #b5b5b5;
            "
          />

          <!-- 
          Next lines of code represent the headers mapping selections.
            It is dynamically generated according to the missing headers.
            The user may have 3 possibilities to map the mandatory header:
            1) Map it with one found in the CSV (1:1 mapping)
            2) Map it with multiple headers found in the CSV (1:N mapping)
            3) Create a new column and do not do any mapping
          -->
          <div v-for="header in missingHeaders" :key="header.name">
            <span class="tag is-info is-large is-light"
              ><label>{{ header.name }}</label></span
            >
            &emsp;

            <!-- Dropdown menu: 1:1 mapping OR create new header -->
            <div v-if="header.type === 'single'" class="select is-link">
              <select
                :name="header.name"
                :id="header.name"
                @change="
                  changeHeaderMapping(
                    $event.target.options[$event.target.options.selectedIndex]
                      .text,
                    header.name
                  )
                "
              >
                <option selected disabled>-</option>
                <option>Create new header</option>
                <option v-for="h in headers" :value="h" :key="h">
                  <div
                    v-if="
                      !mandatoryHeaders.map((header) => header.name).includes(h)
                    "
                  >
                    {{ h }}
                  </div>
                </option>
              </select>
            </div>
            &emsp;
            <span
              v-if="getDefaultValue(header.name)"
              class="tag is-info is-large is-light"
            >
              <label>Def. Value: {{ getDefaultValue(header.name) }}</label>
            </span>

            <!-- List of checkboxes: 1:N mapping -->
            <div v-if="header.type === 'multiple'">
              <br />
              <ul
                class="city__list"
                style="
                  list-style: none;
                  height: 100px;
                  width: 100%;
                  overflow: auto;
                "
              >
                <li v-for="h in headers" :key="h">
                  <input
                    id="chk"
                    type="checkbox"
                    :value="h"
                    :name="header.name"
                    @click="changeHeaderMapping(h, header.name)"
                  />
                  {{ h }}
                </li>
              </ul>
            </div>
            <hr />
          </div>

          <!--
            CSV delimiter selection: the program will parse 
            the file according to this choice
          -->
          <div v-if="extension === 'csv'">
            <label class="label">CSV Separator</label>
            <div class="control" v-for="(v, key) in delimitersList" :key="key">
              <input
                type="radio"
                name="CSVDelimiter"
                :value="v"
                v-model="CSVDelimiter"
                @change="changeCSVDelimiter"
              />
              {{ key }} ({{ v }})
            </div>
          </div>
        </div>
      </div>

      <div class="field" v-if="fileName">
        <hr
          style="
            height: 2px;
            border-width: 0;
            color: gray;
            background-color: #b5b5b5;
          "
        />
        <label class="label">Name</label>
        <div class="control">
          <input
            v-model="form.name"
            class="input"
            type="text"
            required
            placeholder="Name your timeline"
          />
        </div>
        <hr />
      </div>

      <div class="error" v-if="!error.length">
        <div class="field" v-if="fileName && percentCompleted === 0">
          <div class="control">
            <input class="button is-success" type="submit" value="Upload" />
          </div>
        </div>
      </div>
      <!-- Error lists -->
      <div v-else>
        <span v-for="(errorMessage, index) in error" :key="index">
          <article class="message is-danger mb-0">
            <div class="message-body">
              {{ errorMessage }}
            </div>
          </article>
        </span>
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
      <span v-if="percentCompleted === 100"
        >Waiting for request to finish..</span
      >
    </b-progress>
  </div>
</template>
<script>
import ApiClient from "../../utils/RestApiClient";

export default {
  data() {
    return {
      headersString: "", // headers string not formatted (used when changing CSV separator)
      valuesString: [],
      /**
       *  headersMapping: list of object containing the:
       * (i) target header to be modified [key=target],
       * (ii) the source header to be substituted [key=source] and
       * (iii) the default value in case we add a new columns [key=default_value].
       */
      headersMapping: [],
      mandatoryHeaders: [
        { name: "datetime", type: "single" },
        { name: "message", type: "multiple" },
        { name: "timestamp_desc", type: "single" },
      ],
      form: {
        name: "",
        file: "",
      },
      fileName: "",
      error: [],
      percentCompleted: 0,

      CSVDelimiter: ",",
      infoMessage: "",
      delimitersList: { Comma: ",", Semicolon: ";", Pipe: "|" },
      showHelperFlag: false,
      showPreviewFlag: false,
      showAddColumnFlag: false,
      checkedHeaders: [],
      staticNumberRows: 3,
      colors: [
        { name: "red", value: "background-color: #FEECF0; color:#CC0F35" },
        { name: "blue", value: "background-color: #EEF6FC; color:#1D72AA" },
        { name: "green", value: "background-color: #EFFAF3; color:#257942" },
      ],
    };
  },
  computed: {
    headers() {
      let headers = [];
      if (this.extension === "csv") {
        headers = this.headersString.split(this.CSVDelimiter);
      } else if (["json", "jsonl"].includes(this.extension)) {
        headers = Object.keys(this.headersString);
      }
      return headers;
    },
    missingHeaders() {
      return this.mandatoryHeaders.filter(
        (header) => this.headers.indexOf(header.name) < 0
      );
    },
    extension() {
      let extension = this.fileName.split(".")[1];
      if (extension) return extension.toLowerCase();
      else return null;
    },
    numberRows() {
      if (this.extension === "csv") {
        let n = this.valuesString.indexOf("");
        return n < 0 ? this.staticNumberRows : n;
      } else if (["json", "jsonl"].includes(this.extension)) {
        return this.valuesString.length;
      } else {
        return 0;
      }
    },
    allHeaders() {
      let setHeaders = new Set(
        this.mandatoryHeaders.map((x) => x.name).concat(this.headers)
      );
      let headers = [...setHeaders];
      return headers;
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
      let valuesAndHeaders = {};
      if (this.extension === "csv") {
        let values = this.valuesString.map((x) => x.split(this.CSVDelimiter));
        /**
         * values is an array of array (matrix)
         * For example, for a CSV with 3 headers such as datetime, timestamp description and permission
         * E.g., values = | [2022-11-10, file_delete, high] |
         *                | [2022-11-09, file_create, high] |
         *                | [2022-11-09, file_update, low]  |
         */
        for (let i = 0; i < this.headers.length; i++) {
          let listValues = [];
          for (let j = 0; j < values.length; j++) {
            listValues.push(values[j][i]); // list values aggregate the information on the columns
          }
          valuesAndHeaders[this.headers[i]] = listValues;
        }
      } else if (["json", "jsonl"].includes(this.extension)) {
        for (let i = 0; i < this.valuesString.length; i++) {
          for (let header in this.valuesString[i]) {
            if (header in valuesAndHeaders) {
              valuesAndHeaders[header].push(this.valuesString[i][header]);
            } else {
              valuesAndHeaders[header] = [this.valuesString[i][header]];
            }
          }
        }
      }
      let checkedHeaders = this.checkedHeaders;
      return checkedHeaders.sort().map((header) => {
        let color = ""; // CSS property for the displayed column
        let values = []; // values that we will display for the checked header

        if (this.headers.includes(header)) {
          // case 0: the mandatory header is in the CSV (no mapping required)
          values = valuesAndHeaders[header];
          color = this.colors.find((x) => x.name === "blue").value;
        } else {
          // header is missing, need to check to headers mapping
          // case 1: we map the header with only one column -> rename column
          // case 2: we map the header with multiple fields -> combine columns
          // case 3: we want to create a new column with a default value -> create a new column
          // case 4: we haven't mapped the header yet

          // extract from the headersMapping the user's choice (it may be null if the user has not mapped the header yet)
          let extractedMapping = this.headersMapping.find(
            (x) => x.target === header
          );
          if (extractedMapping) {
            if (extractedMapping.source) {
              if (extractedMapping.source.length === 1) {
                // case 1
                values = valuesAndHeaders[extractedMapping.source[0]];
              } else {
                // case 2
                let listSources = extractedMapping.source;
                for (let i = 0; i < this.numberRows; i++) {
                  let concatValue = "";
                  listSources.forEach((source) => {
                    concatValue += source + ": ";
                    concatValue +=
                      JSON.stringify(valuesAndHeaders[source][i]) + " | ";
                  });
                  values.push(concatValue);
                }
              }
            } else {
              // case 3
              values = Array(this.numberRows).fill(
                extractedMapping.default_value
              );
            }
            color = this.colors.find((x) => x.name === "green").value;
          } else {
            // case 4
            values = Array(this.numberRows).fill("Header not mapped");
            color = this.colors.find((x) => x.name === "red").value;
          }
        }
        return { name: header, values: values, color: color };
      });
    },
  },
  methods: {
    showHelper() {
      // first hide the other menus
      this.showPreviewFlag = false;
      this.showAddColumnFlag = false;

      this.showHelperFlag = !this.showHelperFlag;
    },
    showPreview() {
      this.showHelperFlag = false;
      this.showPreviewFlag = !this.showPreviewFlag;
      if (!this.showPreviewFlag) this.showAddColumnFlag = false;
    },
    showAddColumn() {
      this.showAddColumnFlag = !this.showAddColumnFlag;
    },
    getDefaultValue: function (target) {
      let obj = this.headersMapping.find((x) => x["target"] === target);
      if (obj) {
        return obj["default_value"];
      } else {
        return null;
      }
    },
    changeCSVDelimiter: function () {
      this.headersMapping = [];
      this.checkedHeaders = this.mandatoryHeaders.map((x) => x.name);
      this.validateFile();
    },
    changeHeaderMapping: function (source, target) {
      /**
       * Method to map the missing headers.
       * First, it checks some conditions, in particular, the user needs to:
       * 1. map the missing header with any existing one in the CSV,
       * 2. avoid to map 2 or more missing headers with the same existing one,
       * 3. specify a default value in case he chooses to create a new column
       */
      if (!source) return;

      let defaultValue = null;
      let type = this.mandatoryHeaders.filter((h) => h.name === target)[0].type;
      let listSelectedHeaders = []; // -> list of checkbox selected

      if (type === "single") {
        if (source === "Create new header") {
          // ask to the user the default row's value
          source = null;
          do {
            defaultValue = prompt("Insert the default value for this header");
            if (defaultValue.includes(this.CSVDelimiter)) {
              alert(
                `New header value cannot contain CSV separator (found ${this.CSVDelimiter})`
              );
              defaultValue = null;
            }
          } while (!defaultValue);
        }
        listSelectedHeaders = source ? [source] : null;
        this.headersMapping = this.headersMapping.filter(
          (mapping) => mapping["target"] !== target
        );
        this.headersMapping.push({
          target: target,
          source: listSelectedHeaders,
          default_value: defaultValue, // leave snake case for python server code
        });
      } else if (type === "multiple") {
        // extract all ticked checkbox
        let tmp = this.headersMapping.find(
          (mapping) => mapping["target"] === target
        );
        listSelectedHeaders = tmp ? tmp["source"] : [];
        if (listSelectedHeaders.includes(source)) {
          listSelectedHeaders = listSelectedHeaders.filter((x) => x !== source);
        } else {
          listSelectedHeaders.push(source);
        }
        this.headersMapping = this.headersMapping.filter(
          (mapping) => mapping["target"] !== target
        );
        if (listSelectedHeaders.length > 0)
          this.headersMapping.push({
            target: target,
            source: listSelectedHeaders,
            default_value: defaultValue,
          });
      } else {
        return;
      }
      this.validateFile();
    },
    clearFormData: function () {
      this.form.name = "";
      this.form.file = "";
      this.fileName = "";
      this.headersMapping = [];
      this.infoMessage = "";
      this.headersString = "";
      this.valuesString = [];
    },
    submitForm: function () {
      if (!this.validateFile()) {
        return;
      }

      let formData = new FormData();
      formData.append("file", this.form.file);
      formData.append("name", this.form.name);
      formData.append("provider", "WebUpload");
      formData.append("context", this.fileName);
      formData.append("total_file_size", this.form.file.size);
      formData.append("sketch_id", this.$store.state.sketch.id);
      if (["csv", "jsonl", "json"].includes(this.extension)) {
        let hMapping = JSON.stringify(this.headersMapping);
        formData.append("headersMapping", hMapping);
        formData.append("delimiter", this.CSVDelimiter);
      }
      let config = {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: function (progressEvent) {
          this.percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
        }.bind(this),
      };
      ApiClient.uploadTimeline(formData, config)
        .then((response) => {
          this.$store.dispatch("updateSketch", this.$store.state.sketch.id);
          this.$emit("toggleModal");
          this.clearFormData();
          this.percentCompleted = 0;
        })
        .catch((e) => {});
    },
    validateFile: function () {
      this.error = [];
      if (this.form.file.size <= 0) {
        this.error.push("Please select a non empty file");
      }
      let allowedExtensions = ["csv", "json", "jsonl", "plaso"];
      if (!allowedExtensions.includes(this.extension)) {
        this.error.push(
          "Please select a file with a valid extension: " +
            allowedExtensions.toString()
        );
      }
      if (["csv", "jsonl", "json"].includes(this.extension)) {
        // 1. check if mapping is completed, i.e., if the user set all the mandatory headers
        if (this.headersMapping.length !== this.missingHeaders.length) {
          this.error.push(
            "Missing headers: " +
              this.missingHeaders.map((h) => h.name).toString()
          );
        }
        // 2. check for duplicate headers (except from the new header and multiple headers)
        let duplicates = this.headersMapping
          .filter((mapping) => mapping["source"])
          .map((e) => e.source);
        duplicates = duplicates.filter((x) => x.length === 1).map((x) => x[0]); // only mapping 1:1. They will be renamed on the database thus we do not want duplicates
        if (duplicates.length > new Set(duplicates).size) {
          this.error.push(
            `New headers mapping contains duplicates (${duplicates})`
          );
        }
      }
      return this.error.length === 0;
    },
    setFile: function (fileList) {
      /* 1. Initialize the variables */

      if (!fileList[0]) {
        return;
      }
      let fileName = fileList[0].name;
      this.headersMapping = [];
      this.headersString = "";
      this.valuesString = [];
      this.form.file = fileList[0];
      this.form.name = fileName.split(".").slice(0, -1).join(".");
      this.fileName = fileName;
      /* 3. Manage CSV missing headers */
      if (this.extension === "csv") {
        this.extractCSVHeader();
      } else if (["json", "jsonl"].includes(this.extension)) {
        this.extractJSONLHeader();
      } else {
        this.validateFile();
      }
      this.checkedHeaders = this.mandatoryHeaders.map((x) => x.name);
    },
    extractCSVHeader: function () {
      let reader = new FileReader();
      let file = document.getElementById("datafile").files[0];

      // read only 1000 B --> it is reasonable that the header of the CSV file ends before the 1000^ byte.
      // Done to prevent JS reading a large CSV file (GBs)
      let vueJS = this;
      reader.readAsText(file.slice(0, 10000));
      reader.onloadend = function (e) {
        if (e.target.readyState === FileReader.DONE) {
          /* 3a. Extract the headers from the CSV */
          let data = e.target.result;
          vueJS.headersString = data.split("\n")[0].replaceAll('"', "");
          vueJS.valuesString = data
            .split("\n")
            .slice(1, vueJS.staticNumberRows + 1);
          vueJS.validateFile();
        }
      };
    },
    extractJSONLHeader: function () {
      let reader = new FileReader();
      let file = document.getElementById("datafile").files[0];
      let vueJS = this;
      reader.readAsText(file.slice(0, 10000));
      reader.onloadend = function (e) {
        if (e.target.readyState === FileReader.DONE) {
          /* 3a. Extract the headers from the JSONL */
          let data = e.target.result;
          let rows = data.split("\n");
          let i = Math.min(vueJS.staticNumberRows, rows.length);
          try {
            vueJS.headersString = JSON.parse(rows[0]);
            vueJS.valuesString = rows.slice(0, i).map((x) => JSON.parse(x));
            vueJS.validateFile();
          } catch (objError) {
            vueJS.headersString = ""
            vueJS.valuesString = ""
            let error = objError.message;
            error += ". Your first lines of JSON: ";
            error += rows[0];
            vueJS.error.push(error);
            vueJS.error.push("Submit a valid JSONL/Plaso/CSV file")
          }
        }
      };
    },
  },
};
</script>