(function() {
    var module = angular.module('timesketch', [
        'timesketch.api',
        'timesketch.core',
        'timesketch.explore'
    ]);

    // Config
    module.config(function($httpProvider) {
        $httpProvider.interceptors.push(function($q, $rootScope) {
            return {
                'request': function(config) {
                    $rootScope.$broadcast('httpreq-start');
                    return config || $q.when(config);
                },
                'response': function(response) {
                    $rootScope.$broadcast('httpreq-complete');
                    return response || $q.when(response);
                },
                'responseError': function(response) {
                    $rootScope.$broadcast('httpreq-error');
                    return $q.reject(response);
                }
            };
        });
        var csrftoken = document.getElementsByTagName('meta')['csrf-token'].getAttribute('content');
        $httpProvider.defaults.headers.common['X-CSRFToken'] = csrftoken;
    });
})();

