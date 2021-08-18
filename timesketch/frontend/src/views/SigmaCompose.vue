<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content"></div>
          <textarea id="textarea" v-model="text" placeholder="Enter your Sigma yaml File text..." rows="30" cols="80">
title: Suspicious Installation of Zenmap</textarea
          >

          <div class="control">
            <button id="parseButton" v-on:click="parseSigma">Parse</button>
          </div>
          <template>
            <pre>{{ JSON.stringify(parsed, null, 2) }}</pre>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  data() {
    return {
      text: `title: Suspicious Installation of Zenmap2
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of Zenmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
tags:
    - attack.discovery
    - attack.t1046
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install zmap*'
    condition: keywords
falsepositives:
    - Unknown
level: high
      `,
      parsed: '',
    }
  },
  methods: {
    parseSigma: function(event) {
      document.getElementById('parseButton').disabled = true
      ApiClient.getSigmaByText(this.text)
        .then(response => {
          let SigmaRule = response.data.objects[0]
          console.log(SigmaRule)
          this.parsed = SigmaRule
        })
        .catch(e => {})
      document.getElementById('parseButton').disabled = false
    },
    submitForm: function() {
      /*ApiClient.uploadTimeline(formData, config)
        .then(response => {
          this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
          this.$emit('toggleModal')
          this.clearFormData()
          this.percentCompleted = 0
        })
        .catch(e => {})
        */
      console.log('aaa')
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
pre {
  white-space: pre-wrap;
  white-space: -moz-pre-wrap;
  white-space: -pre-wrap;
  white-space: -o-pre-wrap;
  word-wrap: break-word;
}
</style>
