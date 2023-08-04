/*
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
*/
import ApiClient from '../utils/RestApiClient'

export async function fetchActiveAnalyses(sketchId) {
  try {
    const activeAnalyses = []
    const response = await ApiClient.getActiveAnalyzerSessions(sketchId)
    if (response && response.data && response.data.objects && response.data.objects[0]) {
      const activeSessionsDetailed = response.data.objects[0].detailed_sessions
      if (activeSessionsDetailed.length > 0) {
        for (const session of activeSessionsDetailed) {
          activeAnalyses.push(...session.objects[0]['analyses'])
        }
      }
    }
    return activeAnalyses;
  } catch (error) {
    console.error(error);
  }
}

export function updateActiveAnalyses(store, analyses) {
  const activeAnalyses = analyses.filter(a => a.status[0].status === 'PENDING' || a.status[0].status === 'STARTED');
  store.dispatch("updateActiveAnalyses", activeAnalyses)
}
