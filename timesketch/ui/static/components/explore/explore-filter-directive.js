(function() {
    var module = angular.module('timesketch.explore.filter.directive', []);

    module.directive('tsFilter', function () {
        return {
            restrict: 'A',
            templateUrl: '/static/components/explore/explore-filter.html',
            controller: function ($scope) {
                $scope.clearFilter = function() {
                    delete $scope.filter.time_start;
                    delete $scope.filter.time_end;
                    $scope.search()
                };
            }
        }
    });

    module.directive('tsTimelinePickerCard', ['timesketchApi', function(timesketchApi) {
        return {
            restrict: 'A',
            templateUrl: '/static/components/explore/explore-timeline-picker-card.html',
            controller: function ($scope) {
                $scope.enableAll = function() {
                    $scope.filter.indices = [];
                    for (var i = 0; i < $scope.sketch.timelines.length; i++) {
                        $scope.filter.indices.push($scope.sketch.timelines[i].searchindex.index_name)
                    }
                    $scope.search()
                };
                $scope.disableAll = function() {
                    $scope.filter.indices = [];
                    $scope.events = [];
                    $scope.meta.es_total_count = 0;
                    $scope.meta.es_time = 0;
                }
            }
        }
    }]);

    module.directive('tsTimelinePickerItem', function() {
        return {
            restrict: 'A',
            templateUrl: '/static/components/explore/explore-timeline-picker-item.html',
            link: function (scope, elem, attrs) {
                var index_name = scope.timeline.searchindex.index_name;
                scope.toggleCheckbox = function () {
                    var index = scope.filter.indices.indexOf(index_name);
                    scope.checkboxModel = !scope.checkboxModel;
                    if (! scope.checkboxModel) {
                        if (index > -1) {
                            scope.filter.indices.splice(index, 1);
                        }
                    } else {
                        if (index == -1) {
                            scope.filter.indices.push(index_name);
                        }
                    }
                    scope.search();
                };
                scope.$watch("filter", function(value) {
                    if (scope.filter.indices.indexOf(index_name) == -1) {
                        scope.colorbox = {'background-color': '#E9E9E9'};
                        scope.timeline_picker_title = {'color': '#D1D1D1', 'text-decoration': 'line-through'};
                        scope.checkboxModel = false;
                    } else {
                        scope.colorbox = {'background-color': "#" + scope.timeline.color};
                        scope.timeline_picker_title = {'color': '#333', 'text-decoration': 'none'};
                        scope.checkboxModel = true;
                    }
                }, true);
            }
        }
    });

})();
