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
  <v-card width="1000" style="overflow: initial">
    <v-container class="px-8">
      <div v-if="error">
        <v-alert border="right" colored-border type="error" elevation="2"> {{ error }} </v-alert>
      </div>
      <div v-else>
        <v-alert border="top" colored-border type="info" elevation="2"> XML viewer </v-alert>
      </div>
      <v-alert colored-border :color="'success'" border="left" elevation="1">
        <ul style="list-style-type: none">
          <li v-for="item in items" :key="item.id" :style="item.margin">
            <strong>{{ item.name }} </strong> <i style="color: #808080">{{ item.attributes }} </i>:
            <code v-if="item.value.trim().length > 0">{{ item.value }}</code>
          </li>
        </ul>
      </v-alert>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text color="primary" @click="clearAndCancel"> Cancel </v-btn>
      </v-card-actions>
    </v-container>
  </v-card>
</template>

<script>
export default {
  props: ['xmlString'],
  data() {
    return {
      error: null,
      jsonString: null,
      items: [],
      count: 0,
    }
  },
  mounted() {
    let parser = new DOMParser()
    let xmlDoc = parser.parseFromString(this.xmlString, 'text/xml')
    let errorNode = xmlDoc.querySelector('parsererror')
    if (errorNode) {
      this.error = 'Document cannot be formatted correctly... '
    } else {
      this.error = ''
    }
    this.xmlToJson(xmlDoc.childNodes[0], 0)
    this.items.sort((a, b) => (a.id > b.id ? 1 : b.id > a.id ? -1 : 0))
  },
  methods: {
    clearAndCancel: function () {
      this.$emit('cancel')
    },

    xmlToJson: function (node, margin) {
      let marginString = 'margin-left: ' + margin + '%'
      this.count++
      let id = this.count
      let value = ''
      if (node.data && node.data.trim().length === 0) {
        return null
      }
      let name = node.tagName
      let attributes = [...node.attributes]
      let attributesArray = []
      for (let i = 0; i < attributes.length; i++) {
        attributesArray.push(attributes[i].name + ' : ' + attributes[i].value)
      }
      let attributesString = ''
      if (attributesArray.length > 0) attributesString = '( ' + attributesArray.join(' - ') + ' )'

      if (!node.hasChildNodes()) {
        this.items.push({ id: id, name: name, margin: marginString, value: value, attributes: attributesString })
        return
      }

      let nodes = node.childNodes
      let firstChild = nodes[0]
      if (firstChild.data && firstChild.data.trim().length > 0) {
        value = firstChild.data
      } else {
        for (let i = 0; i < nodes.length; i++) {
          this.xmlToJson(nodes[i], margin + 3)
        }
      }
      this.items.push({ id: id, name: name, margin: marginString, value: value, attributes: attributesString })
    },
  },
}
</script>

<style scoped lang="scss"></style>