/*
Copyright 2024 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import dayjs from "@/plugins/dayjs";

export const initialLetter = (input) => {
  if (!input) return "";
  input = input.toString();
  return input.charAt(0).toUpperCase();
};

export const shortDateTime = (date) => {
  return dayjs.utc(date).format("YYYY-MM-DD HH:mm");
};

export const timeSince = (date) => {
  if (!date) {
    return "";
  }
  return dayjs.utc(date).fromNow();
};

export const compactNumber = (input) => {
  if (!input) {
    input = 0;
  }
  let mark = "";
  if (input > 999999999) {
    input = Math.round((input / 1000000000) * 10) / 10;
    mark = "B";
  } else if (input > 999999) {
    input = Math.round((input / 1000000) * 10) / 10;
    mark = "M";
  } else if (input > 999) {
    input = Math.round((input / 1000) * 10) / 10;
    mark = "K";
  } else {
    return input;
  }
  return input + mark;
};

export const formatTimestamp = (input) => {
  if (input === null || input === undefined) {
    return null;
  }
  let tsLength = parseInt(input).toString().length;
  if (tsLength === 13) {
    return input; // exit early if timestamp is already in milliseconds
  } else if (tsLength === 15 || tsLength === 16) {
    input = input / 1000; // microseconds -> milliseconds
  } else if (tsLength === 10) {
    input = input * 1000; // seconds -> milliseconds
  }
  return parseInt(input);
};

export const toISO8601 = (timestampMillis) => {
  if (timestampMillis === null || timestampMillis === undefined) {
    return null;
  }
  if (timestampMillis < 0) {
    return "No timestamp";
  }
  return dayjs(timestampMillis).toISOString();
};

export const formatSeconds = (seconds) => {
  if (seconds > 60) {
    return seconds / 60 + "m";
  }
  return seconds + "s";
};

export const formatLabelText = (input) => {
  if (input === "__ts_star" || input === "label : __ts_star") {
    return "All starred events";
  }
  if (input === "__ts_comment" || input === "label : __ts_comment") {
    return "All commented events";
  }
  return input.replace("__ts_", "");
};

export const compactBytes = (input) => {
  // Based on https://gist.github.com/james2doyle/4aba55c22f084800c199
  if (!input) {
    input = 0
  }
  let units = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  let exponent = Math.min(Math.floor(Math.log(input) / Math.log(1000)), units.length - 1)
  let num = (input / Math.pow(1000, exponent)).toFixed(2) * 1
  return num + units[exponent]
}
