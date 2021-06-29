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
    <b-table
        v-if="sigmaRuleList"
        :data="sigmaRuleList"
        :current-page.sync="currentPage"
        :per-page="perPage"
        paginated
        pagination-simple
        pagination-position="bottom"
        default-sort-direction="desc"
        sort-icon="arrow-down"
        sort-icon-size="is-small"
        icon-pack="fas"
        icon-prev="chevron-left"
        icon-next="chevron-right"
        default-sort="title"
      >

      <b-table-column field="id" 
        label="Rule ID" 
        v-slot="props" 
        sortable searchable>
          {{ props.row.id }} 
          <span class="icon is-small"
                style="cursor:pointer;float:right;"
                title="Copy value"
                v-on:click="copyCode(props.row.id)">
          <i class="fas fa-copy"></i></span>
          <span class="icon is-small">
                <router-link :to="{ name: 'SigmaContent', query: {ruleId: props.row.id }}"
                   ><i class="fas fa-search">aaaaaaa</i></router-link></span>
          <span
                class="icon is-small"
                style="cursor:pointer;float:right;"
                title="Explore"
                v-on:click="openSigmaRule(props.row.id)">
          <i class="fas fa-search"></i></span>
        </b-table-column>
        <b-table-column field="title" label="Title" v-slot="props" sortable searchable>
          {{ props.row.title }} <span class="icon is-small"
                style="cursor:pointer;float:right;"
                title="Copy value"
                v-on:click="copyCode(props.row.title)"
                ><i class="fas fa-copy"></i></span>
        </b-table-column>
        <b-table-column field="es_query" label="ES Query" v-slot="props" sortable searchable>
          {{ props.row.es_query }}
                <span class="icon is-small">
                <router-link :to="{ name: 'Explore', query: {q : props.row.es_query} }"
                   ><i class="fas fa-search"></i></router-link></span>
                <span class="icon is-small"
                style="cursor:pointer;float:right;"
                title="Copy value"
                v-on:click="copyCode(props.row.es_query)"
                ><i class="fas fa-copy"></i></span>
        </b-table-column>
        <b-table-column field="file_name" label="File Name" v-slot="props" sortable searchable>
          {{ props.row.file_name }} <span 
                class="icon is-small" 
                @mouseover="hover = true"
                @mouseleave="hover = false"
                :class="{ active: hover }"
                style="cursor:pointer;float:right;"
                title="Copy value"
                v-on:click="copyCode(props.row.file_name)"
                ><i class="fas fa-copy"></i></span>
                <span class="icon is-small">
                <router-link
                      :to="{ name: 'Explore', query: {q : props.row.file_name} }"
                   ><i class="fas fa-search"></i></router-link></span>
        </b-table-column>
        <b-table-column field="tags" label="Tag" v-slot="props" sortable searchable>
          <ul class="content-list">
            <li style="padding:10px;border-bottom:none;cursor:pointer;">
              <div v-for="tag in props.row.tags" v-bind:key="tag">
                {{ tag }} 
                <span class="icon is-small">
                <router-link
                      :to="{ name: 'Explore', query: {q : tag} }"
                   ><i class="fas fa-search"></i></router-link></span>
            </div>
            </li>
          </ul>
        </b-table-column>
      </b-table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      currentPage: 1,
      ascending: false,
      sortColumn: '', 
      perPage: 10,
      upHere : false,
      hover : false     
    }
  },
  methods: {
    copyCode: function (value) {
          const el = document.createElement('textarea');
          el.value = value;
          document.body.appendChild(el);
          el.select();
          document.execCommand('copy');
          this.$buefy.notification.open('Copied')
          document.body.removeChild(el);
    }
  },
  computed: {
    sigmaRuleList() {
      return this.$store.state.sigmaRuleList
    },
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {
    this.sigmaRuleList_count = this.$store.state.sigmaRuleList_count
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
span {
  background: red;
}
span:hover {
  background: green;
  visibility: visible;
}
</style>
