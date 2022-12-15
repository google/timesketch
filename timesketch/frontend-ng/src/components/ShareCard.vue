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
  <v-card class="pa-4">
    <h2>Share "{{ sketch.name }}"</h2>
    <br />
    <v-autocomplete
      v-model="usersToAdd"
      :items="systemUsers"
      outlined
      single-line
      chips
      small-chips
      hide-details
      label="Add people and groups"
    ></v-autocomplete>
    <br />
    People with access
    <br />
    General access
    <v-select
      hide-details
      single-line
      :items="items"
      :label="currentAccess"
      :prepend-icon="icon"
      style="width: 150px"
    ></v-select>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  data() {
    return {
      items: ['Public', 'Restricted'],
      systemUsers: [],
      systemGroups: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    currentAccess() {
      if (this.meta.permissions.public) {
        return 'Public'
      }
      return 'Restricted'
    },
    icon() {
      if (this.meta.permissions.public) {
        return 'mdi-globe'
      }
      return 'mdi-earth'
    },
  },
  methods: {},
  mounted() {
    ApiClient.getUsers()
      .then((response) => {
        response.data.objects[0].forEach((user) => {
          this.systemUsers.push(user.username)
        })
      })
      .catch((e) => {})
    ApiClient.getGroups()
      .then((response) => {
        response.data.objects[0].forEach((group) => {
          this.systemGroups.push(group.name)
        })
      })
      .catch((e) => {})
  },
}
</script>

<!-- CSS scoped to this component only -->
<style lang="scss">
.v-text-field > .v-input__control > .v-input__slot:before {
  border-style: none;
}
.v-text-field > .v-input__control > .v-input__slot:after {
  border-style: none;
}
</style>
