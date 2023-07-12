import ApiClient from '../utils/RestApiClient'

export async function fetchAndUpdateActiveAnalyses(store, sketchId) {
  try {
    const response = await ApiClient.getActiveAnalyzerSessions(sketchId)
    const activeSessionsDetailed = response.data.objects[0].detailed_sessions
    const activeAnalyses = []
    if (activeSessionsDetailed.length > 0) {
      for (const session of activeSessionsDetailed) {
        activeAnalyses.push(...session.objects[0]['analyses'])
      }
    }
    updateActiveAnalyses(store, activeAnalyses)
    return activeAnalyses;
  } catch (error) {
    console.error(error);
  }
}

export function updateActiveAnalyses(store, analyses) {
  const activeAnalyses = analyses.filter(a => a.status[0].status === 'PENDING' || a.status[0].status === 'STARTED');
  store.dispatch("updateActiveAnalyses", activeAnalyses)
}
