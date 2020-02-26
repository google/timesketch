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

  <form v-on:submit.prevent="">
    <div class="field">
      <div class="control">

        <b-radio v-model="isPublic" type="is-info" name="name" native-value="false">
          <i class="fa fa-lock" style="margin-left: 10px;margin-right: 5px;"></i>
          Private - Only you and selected users/groups can access this sketch
        </b-radio>
        <br>
        <b-radio v-model="isPublic" type="is-info" name="name" native-value="true">
          <i class="fa fa-globe" style="margin-left: 10px;margin-right: 5px;"></i>
          Public -  All users of the system can access this sketch
        </b-radio>

        <hr>

        <div v-if="currentUsers.length || currentGroups.length">
          Who has access
          <br><br>
          <table class="table is-hoverable">
            <tr v-for="(user, index) in currentUsers">
              <td>{{ user }}</td>
              <td width="10px" style="cursor: pointer;" v-on:click="removeUser(user, index)"><i class="fa fa-trash"></i></td>
            </tr>
            <tr v-for="(group, index) in currentGroups">
              <td>{{ group }}</td>
              <td width="10px" style="cursor: pointer;" v-on:click="removeGroup(group, index)"><i class="fa fa-trash"></i></td>
            </tr>
          </table>
          <br><br>
        </div>

        <b-notification v-if="usersToRemove.length || groupsToRemove.length" type="is-warning" role="alert" :closable=false>
          You have made changes that you need to save
        </b-notification>

        <b-field label="Share with user">
          <b-autocomplete
            clear-on-select
            v-model="userNameInput"
            :data="filteredUserArray"
            placeholder="Username .."
            icon="magnify"
            @select="addUser">
            <template slot="empty">No user found</template>
          </b-autocomplete>
        </b-field>
      </div>
    </div>

    <div class="field">
      <div class="control">
        <b-field label="Share with group">
          <b-autocomplete
            clear-on-select
            open-on-focus
            v-model="groupNameInput"
            :data="filteredGroupArray"
            placeholder="Group name .."
            icon="magnify"
            @select="addGroup">
            <template slot="empty">No group found</template>
          </b-autocomplete>
        </b-field>
      </div>
    </div>

    <div v-if="usersToAdd.length || groupsToAdd.length">
      <br>
      <strong>Users/Groups to add</strong>
      <br><br>
      <b-field grouped group-multiline>
        <div class="control" v-for="(user, index) in usersToAdd" :key="user.name">
          <b-tag attached closable aria-close-label="Close tag" size="is-medium" @close="usersToAdd.splice(index, 1)">{{ user }}</b-tag>
        </div>
        <div class="control" v-for="(group, index) in groupsToAdd" :key="group.name">
          <b-tag attached closable aria-close-label="Close tag" size="is-medium" @close="groupsToAdd.splice(index, 1)">{{ group }}</b-tag>
        </div>
      </b-field>
    </div>

    <br>

    <div class="field">
      <div class="control">
        <button class="button is-info" v-on:click="submitForm">Save changes</button>
      </div>
    </div>

  </form>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data () {
    return {
      isPublic: false,
      systemUsers: [],
      systemGroups: [],
      usersToAdd: [],
      groupsToAdd: [],
      usersToRemove: [],
      groupsToRemove: [],
      userNameInput: '',
      groupNameInput: ''
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    currentUsers() {
      return this.meta.collaborators.users.filter(f => !this.usersToRemove.includes(f));
    },
    currentGroups() {
      return this.meta.collaborators.groups.filter(f => !this.groupsToRemove.includes(f));
    },
    filteredUserArray() {
      return this.systemUsers.filter((option) => {
        return option
          .toString()
          .toLowerCase()
          .indexOf(this.userNameInput.toLowerCase()) >= 0
      })
    },
    filteredGroupArray() {
      return this.systemUsers.filter((option) => {
        return option
          .toString()
          .toLowerCase()
          .indexOf(this.groupNameInput.toLowerCase()) >= 0
      })
    }
  },
  methods: {
    addUser: function (userName) {
      if (userName) {
        if (!this.usersToAdd.includes(userName)) {
          this.usersToAdd.push(userName)
        }
      }
    },
    addGroup: function (groupName) {
      if (!this.groupsToAdd.includes(groupName)) {
        this.groupsToAdd.push(groupName)
      }
    },
    removeUser: function (userName, index) {
      this.usersToRemove.push(userName)
    },
    removeGroup: function (groupName, index) {
      this.groupsToRemove.push(groupName)
    },
    submitForm: function () {
      ApiClient.editCollaborators(this.sketch.id, this.isPublic, this.usersToAdd, this.groupsToAdd, this.usersToRemove, this.groupsToRemove).then((response) => {}).catch((e) => {})
      this.$emit('closeShareModal')
    }
  },
  mounted() {
    if (this.meta.permissions.public) {
      this.isPublic = true
    }
    ApiClient.getUsers().then((response) => {
      response.data.objects[0].forEach((user => {
        this.systemUsers.push(user.username)
      }))
    }).catch((e) => {})
    ApiClient.getGroups().then((response) => {
      response.data.objects[0].forEach((group => {
        this.systemGroups.push(group.name)
      }))
    }).catch((e) => {})
  }
}
</script>
