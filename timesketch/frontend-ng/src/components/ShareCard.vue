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
  <v-card :loading="isLoading">
    <div class="pa-4">
      <h3>Share "{{ sketch.name }}"</h3>
      <br />
      <v-autocomplete
        v-model="usersAndGroupsToAdd"
        :items="usersAndGroups"
        outlined
        single-line
        chips
        small-chips
        hide-details
        multiple
        return-object
        deletable-chips
        label="Add people and groups"
      ></v-autocomplete>
      <br />
      People with access
      <v-list>
        <v-list-item>
          <v-list-item-avatar>
            <v-avatar color="grey lighten-1" size="32">
              <span class="white--text">{{ sketch.user.username | initialLetter }}</span>
            </v-avatar>
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title v-text="sketch.user.username"></v-list-item-title>
          </v-list-item-content>
          <v-spacer></v-spacer>
          <small>Owner</small>
        </v-list-item>
        <v-list-item v-for="user in meta.collaborators.users" :key="user">
          <v-list-item-avatar>
            <v-avatar color="grey lighten-1" size="32">
              <span class="white--text">{{ user | initialLetter }}</span>
            </v-avatar>
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title v-text="user"></v-list-item-title>
          </v-list-item-content>
          <v-spacer></v-spacer>
          <v-icon @click="revokeAccess(user, '')">mdi-trash-can-outline</v-icon>
        </v-list-item>
        <v-list-item v-for="group in meta.collaborators.groups" :key="group">
          <v-list-item-avatar>
            <v-icon>mdi-account-group-outline</v-icon>
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title v-text="group"></v-list-item-title>
          </v-list-item-content>
          <v-spacer></v-spacer>
          <v-icon @click="revokeAccess('', group)">mdi-trash-can-outline</v-icon>
        </v-list-item>
      </v-list>
      <br />
      General access
      <v-select
        hide-details
        single-line
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

export default {
  data() {
    return {
      items: [
        {
          text: 'Public',
          value: true,
        },
        {
          text: 'Restricted',
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
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
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
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
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
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
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
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
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
            text: user.username,
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
            text: group.name,
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
