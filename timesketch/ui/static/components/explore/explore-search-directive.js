(function() {
    var module = angular.module('timesketch.explore.search.directive', []);

    module.directive('tsSearch', ['$location', 'timesketchApi', function($location, timesketchApi) {
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-search.html',
            scope: {
                sketchId: '=',
                viewId: '='
            },
            link: function(scope, elem, attrs) {
                if (attrs.autoload == 'true') {
                    timesketchApi.getView(attrs.sketchId, attrs.viewId).success(function(data) {
                        scope.query = data.objects[0].query_string;
                        scope.filter = angular.fromJson(data.objects[0].query_filter);
                        scope.search();
                    });
                }
                if (attrs.redirect == 'true') {
                    scope.redirectView = true;
                }
            },
            controller: function($scope) {
                $scope.filter = {"indices": []};

                timesketchApi.getSketch($scope.sketchId).success(function(data) {
                    $scope.sketch = data.objects[0];
                    $scope.sketch.views = data.meta.views;
                    $scope.filter.indices = [];
                        for (var i = 0; i < $scope.sketch.timelines.length; i++) {
                            $scope.filter.indices.push($scope.sketch.timelines[i].searchindex.index_name)
                        }
                });

                $scope.search = function() {
                    $scope.events = [];
                    if ($scope.filter.star && $scope.query) {
                        $scope.filter.star = false;
                    }
                    if (!$scope.filter.star && !$scope.query) {
                        return
                    }
                    if ($scope.filter.time_start) {
                        $scope.showFilters = true;
                    }
                    timesketchApi.search($scope.sketchId, $scope.query, $scope.filter)
                        .success(function(data) {
                            $scope.events = data.objects;
                            $scope.meta = data.meta;
                            if (data.meta.es_total_count > 500) {
                                $scope.meta.noisy = true
                            }
                    })
                };

                $scope.search_starred = function() {
                    $scope.filter.star = true;
                    $scope.query = "";
                    $scope.filter.time_start = "";
                    $scope.filter.time_end = "";
                    $scope.search()
                };

                $scope.saveView = function() {
                    timesketchApi.saveView(
                        $scope.sketchId, $scope.view_name, $scope.query, $scope.filter)
                        .success(function(data) {
                            var view_id = data.objects[0].id;
                            var view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/';
                            window.location.href = view_url;
                    });
                }
            }
        }
    }]);

    module.directive('tsSearchSavedViewPicker', ['timesketchApi', function(timesketchApi) {
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-search-saved-view-picker.html',
            scope: false,
            link: function (scope, elem, attrs, ctrl) {
                scope.selectedView = {};
                scope.$watch('selectedView.view', function(value) {
                    if (angular.isDefined(scope.selectedView.view)) {
                        if (angular.isDefined(scope.redirectView)) {
                            var view_url = '/sketch/' + scope.sketchId + '/explore/view/' + scope.selectedView.view.id + '/';
                            window.location.href = view_url;
                        } else {
                            timesketchApi.getView(scope.sketchId, scope.selectedView.view.id).success(function(data) {
                                scope.query = data.objects[0].query_string;
                                scope.filter = angular.fromJson(data.objects[0].query_filter);
                                scope.search()
                            });
                        }
                    }
                })
            }
        }
    }]);

})();

