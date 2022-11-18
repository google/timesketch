<!--
Copyright 2022 Google Inc. All rights reserved.

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
    <b-tag class="rich-attribute-tag" size="is-medium" type="is-success is-light" @click="showDetails = !showDetails">
      <span :title="'Added by: ' + item.source">{{ item.source.startsWith("analyzer") ? "🤖" : "🧠" }}</span>
      {{ name.replace("__", "") }}
      <i class="fas" :class="{ 'fa-plus': !showDetails, 'fa-minus': showDetails }"></i>
    </b-tag>

    <div class="rich-attribute" v-if="showDetails">
      <table class="attribute-details">
        <tr>
          <td>Type</td>
          <td>
            <samp>{{ item.type }}</samp>
          </td>
        </tr>
        <tr>
          <td>Added by</td>
          <td>
            <samp>{{ item.source.split(":")[1] }}</samp> ({{ item.source.split(":")[0] }})
          </td>
        </tr>
      </table>
      <table class="table is-bordered">
        <tbody>
          <tr v-for="key in relevantKeys" v-bind:key="key">
            <td>
              <i
                @click="updateSearch(`_exists_:&quot;*${key}*&quot;`)"
                class="fas fa-search keysearch"
                aria-hidden="true"
                :title="`Search sketch for all events having a '${key}' key.`"
              ></i>
              {{ key }}
            </td>
            <td v-if="isSimpleAttribute(item[key])">
              <b-tag size="is-small">{{ formatSimpleAttribute(item[key]) }}</b-tag>
            </td>
            <td v-else-if="typeof item[key] === 'string'">
              <i
                @click="updateSearch(generateOpenSearchQuery(item[key], key))"
                class="fas fa-search keysearch"
                aria-hidden="true"
                :title="`Search sketch for all events containing this '${key}' value.`"
              ></i>
              <samp>{{ item[key] }}</samp>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: "_all",
    order: "asc",
    chips: [],
  }
}

export default {
  name: "RichAttribute",
  components: {},
  props: ["item", "name"],
  data() {
    return {
      hidden: ["type", "source"],
      showDetails: false,
    }
  },
  computed: {
    relevantKeys() {
      return Object.keys(this.item).filter((key) => !this.hidden.includes(key))
    },
  },
  methods: {
    isSimpleAttribute: function (item) {
      return Object.keys(item)[0].startsWith("__") && Object.values(item)[0].value !== undefined
    },
    formatSimpleAttribute: function (item) {
      let contents = Object.values(item)[0]
      return `${contents.type}: ${contents.value}`
    },
    generateOpenSearchQuery: function (value, field) {
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, "\\$&")
      if (field !== undefined) {
        query = `${this.name}.${field}:${query}`
      }
      return query
    },
    updateSearch: function (query) {
      console.log(query)
      let eventData = {
        doSearch: true,
        queryString: query,
        queryFilter: defaultQueryFilter(),
      }
      this.$emit("setQueryAndFilter", eventData)
    },
  },
}
</script>

<style scoped lang="scss">
.rich-attribute {
  margin: 15px 0 15px 0;
}

.rich-attribute-tag {
  cursor: pointer;
}

.attribute-details td {
  padding: 0 10px 0 0;
}
.attribute-details {
  margin-bottom: 10px;
}

i.keysearch {
  cursor: pointer;
  margin-right: 5px;
}
</style>
