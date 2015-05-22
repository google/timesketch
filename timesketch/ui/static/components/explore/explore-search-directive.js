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
            controller: function($scope) {
                $scope.filter = {"indices": []};

                timesketchApi.getSketch($scope.sketchId).success(function(data) {
                    var sketch = data.objects[0];
                    for (var i = 0; i < sketch.timelines.length; i++) {
                        var timeline = sketch.timelines[i].searchindex.index_name;
                        $scope.filter.indices.push(timeline)
                    }
                    $scope.sketch = sketch
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
                    })
                };


            }


        }
    }]);



})();

