<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-card :loading="isLoading">
    <div class="pa-4">
      <h3>Share "{{ sketch.name }}"</h3>
      <br />
      <v-autocomplete
        label="Add people and groups"
        v-model="usersAndGroupsToAdd"
        :items="usersAndGroups"
        variant="outlined"
        chips
        small-chips
        hide-details
        multiple
        return-object
        closable-chips
      ></v-autocomplete>
      <br />
      People with access
      <v-list>
        <v-list-item :title="sketch.user.username">
          <template v-slot:prepend>
            <v-avatar class="bg-grey-lighten-1" size="32">
              <span class="text-white">{{ $filters.initialLetter(sketch.user.username) }}</span>
            </v-avatar>
          </template>
          <template v-slot:append>
            <small>Owner</small>
          </template>
        </v-list-item>
        <v-list-item v-for="user in meta.collaborators.users" :key="user" :title="user">
          <template v-slot:prepend>
            <v-avatar class="bg-grey-lighten-1" size="32">
              <span class="text-white">{{ $filters.initialLetter(user) }}</span>
            </v-avatar>
          </template>
          <template v-slot:append>
          <v-icon @click="revokeAccess(user, '')">mdi-trash-can-outline</v-icon>
          </template>
        </v-list-item>
        <v-list-item v-for="group in meta.collaborators.groups" :key="group" prepend-icon="mdi-account-group-outline" :title="group">
          <template v-slot:append>
            <v-icon @click="revokeAccess('', group)">mdi-trash-can-outline</v-icon>
          </template>
        </v-list-item>
      </v-list>
      <br />
      General access
      <v-select
        hide-details
        single-line
        variant="plain"
        :items="items"
        v-model="isPublic"
        :label="generalAccess"
        :prepend-icon="accessIcon"
        style="width: 150px"
        @change="setPublicAccess()"
      ></v-select>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="$emit('close-dialog')">Cancel</v-btn>
        <v-btn color="primary" depressed @click="grantAccess()">Done</v-btn>
      </v-card-actions>
    </div>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import { useAppStore } from "@/stores/app";

export default {
  data() {
    return {
      appStore: useAppStore(),
      items: [
        {
          title: 'Public',
          value: true,
        },
        {
          title: 'Restricted',
          value: false,
        },
      ],
      usersAndGroupsToAdd: [],
      usersToRemove: [],
      groupsToRemove: [],
      systemUsers: [],
      systemGroups: [],
      isPublic: false,
      isLoading: false,
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    meta() {
      return this.appStore.meta
    },
    generalAccess() {
      if (this.isPublic) {
        return 'Public'
      }
      return 'Restricted'
    },
    accessIcon() {
      if (this.isPublic) {
        return 'mdi-earth'
      }
      return 'mdi-lock-outline'
    },
    usersAndGroups() {
      return this.systemUsers.concat(this.systemGroups)
    },
  },
  methods: {
    grantAccess: function () {
      if (!this.usersAndGroupsToAdd.length) {
        this.$emit('close-dialog')
        return
      }
      this.isLoading = true
      let usersToAdd = this.usersAndGroupsToAdd
        .filter((user) => user.type === 'user')
        .map((userObject) => userObject.value)
      let groupsToAdd = this.usersAndGroupsToAdd
        .filter((group) => group.type === 'group')
        .map((groupObject) => groupObject.value)
      ApiClient.grantSketchAccess(this.sketch.id, usersToAdd, groupsToAdd)
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id).then(() => {
            this.isLoading = false
            this.usersAndGroupsToAdd = []
            this.$emit('close-dialog')
            this.successSnackBar('Updated sharing')
          })
        })
        .catch((e) => {
          this.errorSnackBar('Failed to share sketch ' + e)
        })
    },
    revokeAccess: function (userName, groupName) {
      this.isLoading = true
      let userToRemove = [userName]
      let groupToRemove = [groupName]
      ApiClient.revokeSketchAccess(this.sketch.id, userToRemove, groupToRemove)
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id).then(() => {
            this.isLoading = false
          })
        })
        .catch((e) => {
          this.errorSnackBar('Failed to remove access ' + e)
        })
    },
    setPublicAccess: function () {
      this.isLoading = true
      ApiClient.setSketchPublicAccess(this.sketch.id, this.isPublic)
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id).then(() => {
            this.isLoading = false
          })
        })
        .catch((e) => {
          this.errorSnackBar('Failed to share sketch ' + e)
        })
    },
  },
  mounted() {
    // Get current sketch access
    this.isPublic = this.meta.permissions.public

    ApiClient.getUsers()
      .then((response) => {
        response.data.objects[0].forEach((user) => {
          let userObject = {
            title: user.username,
            value: user.username,
            type: 'user',
            disabled: false,
          }
          this.systemUsers.push(userObject)
        })
      })
      .catch((e) => {})
    ApiClient.getGroups()
      .then((response) => {
        response.data.objects[0].forEach((group) => {
          let groupObject = {
            title: group.name,
            value: group.name,
            type: 'group',
            disabled: false,
          }

          this.systemGroups.push(groupObject)
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
