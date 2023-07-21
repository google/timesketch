<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-card outlined>
    <v-toolbar dense flat>
      <v-toolbar-title style="font-size: 1.2em">Comments</v-toolbar-title>
    </v-toolbar>

    <v-list three-line>
      <v-list-item
        v-for="(comment, index) in comments"
        :key="comment.id"
        @mouseover="selectComment(comment)"
        @mouseleave="unSelectComment()"
      >
        <v-list-item-avatar>
          <v-avatar color="grey lighten-1">
            <span class="white--text">{{ comment.user.username | initialLetter }}</span>
          </v-avatar>
        </v-list-item-avatar>

        <v-list-item-content>
          <v-list-item-title>
            {{ comment.user.username }}
          </v-list-item-title>
          <v-list-item-subtitle>
            {{ comment.created_at | shortDateTime }} ({{ comment.created_at | timeSince }})
          </v-list-item-subtitle>

          <v-card flat v-if="comment.editable" class="mt-5">
            <v-textarea v-model="comments[index].comment" hide-details auto-grow filled></v-textarea>

            <v-card-actions v-if="comment.editable">
              <v-spacer></v-spacer>
              <v-btn text color="primary" v-if="comment.editable" @click="editComment(index, false)"> Cancel </v-btn>
              <v-btn text color="primary" @click="updateComment(comment, index)"> Save </v-btn>
            </v-card-actions>
          </v-card>
          <p v-else style="max-width: 90%" class="body-2">{{ comment.comment }}</p>
        </v-list-item-content>

        <v-list-item-action
          v-if="comment === selectedComment && meta.permissions.write && currentUser == comment.user.username"
          style="position: absolute; right: 0"
        >
          <v-chip outlined style="margin-right: 10px">
            <v-btn icon small @click="editComment(index)">
              <v-icon small>mdi-square-edit-outline</v-icon>
            </v-btn>
            <v-btn icon small @click="deleteComment(comment.id, index)">
              <v-icon small>mdi-trash-can-outline</v-icon>
            </v-btn>
          </v-chip>
        </v-list-item-action>
      </v-list-item>
    </v-list>

    <v-card-actions v-if="meta.permissions.write">
      <v-textarea
        v-model="comment"
        hide-details
        auto-grow
        filled
        class="mx-2 mb-2"
        label="Add comment"
        rows="1"
      ></v-textarea>
      <v-btn icon @click="postComment">
        <v-icon>mdi-send</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import EventBus from '../../main'
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['comments', 'event', 'currentSearchNode'],
  data() {
    return {
      comment: '',
      selectedComment: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    currentUser() {
      return this.$store.state.currentUser
    },
  },
  methods: {
    postComment: function () {
      EventBus.$emit('eventAnnotated', { type: '__ts_comment', event: this.event, searchNode: this.currentSearchNode })
      ApiClient.saveEventAnnotation(this.sketch.id, 'comment', this.comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.comments.push(response.data.objects[0][0])
          this.event._source.comment.push(this.comment)
          this.comment = ''
        })
        .catch((e) => {})
    },
    updateComment: function (comment, commentIndex) {
      ApiClient.updateEventAnnotation(this.sketch.id, 'comment', comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.comments.splice(commentIndex, 1, comment)
          comment.editable = false
        })
        .catch((e) => {
          console.error(e)
        })
    },
    deleteComment: function (commentId, commentIndex) {
      if (confirm('Are you sure?')) {
        ApiClient.deleteEventAnnotation(this.sketch.id, 'comment', commentId, this.event, this.currentSearchNode)
          .then((response) => {
            this.comments.splice(commentIndex, 1)
            this.event._source.comment.splice(commentIndex, 1)
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    editComment(commentIndex, enable = true) {
      const changeComment = this.comments[commentIndex]
      changeComment.editable = enable
      this.comments.splice(commentIndex, 1, changeComment)
    },
    selectComment(comment) {
      this.selectedComment = comment
    },
    unSelectComment() {
      this.selectedComment = false
    },
  },
}
</script>
