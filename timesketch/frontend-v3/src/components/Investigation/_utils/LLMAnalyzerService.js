/*
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
*/
import RestApiClient from "@/utils/RestApiClient";

const ANALYZER_NAME = 'llm_log_analyzer';
const POLLING_INTERVAL_MS = 5000;

class LLMAnalyzerService {
    constructor(sketchId, store) {
        this.sketchId = sketchId;
        this.store = store;
        this.pollingInterval = null;
    }

    /**
     * Checks if the specific LLM log analyzer is currently running for the sketch.
     * @returns {Promise<boolean>}
     */
    async isActive() {
        if (!this.store.sketch.timelines || !this.store.sketch.timelines.length) {
            return false;
        }
        try {
            const response = await RestApiClient.getActiveAnalyzerSessions(this.sketchId);
            const detailedSessions = response.data?.objects?.[0]?.detailed_sessions || [];
            return detailedSessions.some(session =>
                session.objects?.[0]?.analyses?.some(analysis => analysis.analyzer_name === ANALYZER_NAME)
            );
        } catch (e) {
            console.error('Error fetching active analyzer sessions:', e);
            return false;
        }
    }

    /**
     * Starts the LLM log analysis.
     * @param {function} onComplete - Callback function to execute when analysis is complete.
     * @param {function} onUpdate - Callback function to execute on each poll that finds the analyzer is still active.
     */
    async startAnalysis(onComplete, onUpdate) {
        if (!this.sketchId) {
            console.error("Sketch ID is missing.");
            return;
        }

        const timelineIds = this.store.sketch.timelines.map(tl => tl.id);
        if (!timelineIds.length) {
            this.store.setNotification({
                text: 'There are no timelines in this sketch to analyze.',
                icon: 'mdi-alert-circle-outline',
                type: 'error',
            });
            return;
        }

        this.store.setNotification({
            text: 'AI analysis has started. Findings will appear as they are discovered.',
            icon: 'mdi-clock-start',
            type: 'info',
        });

        try {
            // The analyzer only needs one timeline ID to run against the whole sketch.
            await RestApiClient.runAnalyzers(this.sketchId, [timelineIds[0]], [ANALYZER_NAME], true);
            this._startPolling(onComplete, onUpdate);
        } catch (error) {
            this.store.setNotification({
                text: 'An error occurred when trying to start the AI analysis.',
                icon: 'mdi-alert-circle-outline',
                type: 'error',
            });
            console.error('Error starting log analyzer:', error);
            // Ensure the onComplete callback is called to reset UI state
            if (onComplete) onComplete();
        }
    }

    /**
     * Starts the polling mechanism to check for analysis completion.
     * @param {function} onComplete - Callback for completion.
     * @param {function} onUpdate - Callback for progress updates.
     */
    _startPolling(onComplete, onUpdate) {
        this.stopPolling(); // Ensure no multiple polling loops are running

        this.pollingInterval = setInterval(async () => {
            try {
                const isRunning = await this.isActive();
                if (isRunning) {
                    if (onUpdate) onUpdate();
                } else {
                    this.stopPolling();
                    this.store.setNotification({
                        text: 'AI analysis complete. All questions have been generated.',
                        icon: 'mdi-check-circle-outline',
                        type: 'success',
                    });
                    if (onComplete) onComplete();
                }
            } catch (error) {
                console.error('Error during analyzer polling:', error);
                this.stopPolling();
                this.store.setNotification({
                    text: 'An error occurred while checking analyzer status.',
                    icon: 'mdi-alert-circle-outline',
                    type: 'error',
                });
                if (onComplete) onComplete(); // Also call onComplete on error
            }
        }, POLLING_INTERVAL_MS);
    }

    /**
     * Stops the polling interval.
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}

export default LLMAnalyzerService;
