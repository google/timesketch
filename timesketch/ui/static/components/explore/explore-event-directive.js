(function() {
    var module = angular.module('timesketch.explore.event.directive', []);

    module.directive('tsEventList', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-event-list.html',
            scope: {
                sketchId: '=',
                meta: '=',
                events: '='
            }
        }
    });

    module.directive('tsEvent', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-event.html',
            scope: {
                sketchId: '=',
                meta: '=',
                event: '='
            },
            controller: function ($scope, timesketchApi) {
                $scope.star = false;
                if ($scope.event._source.label.indexOf('__ts_star') > -1) {
                    $scope.star = true;
                    $scope.event._source.label.splice($scope.event._source.label.indexOf('__ts_star'), 1)
                }

                if ($scope.event._source.label.indexOf('__ts_comment') > -1) {
                    $scope.comment = true;
                    $scope.event._source.label.splice($scope.event._source.label.indexOf('__ts_comment'), 1)
                }

                $scope.toggleStar = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'label',
                        '__ts_star',
                        $scope.event._index,
                        $scope.event._id,
                        $scope.event._type).success(function(data) {})
                };
                $scope.getDetail = function() {
                    if ($scope.eventdetail) {return}
                    timesketchApi.getEvent(
                        $scope.sketchId,
                        $scope.event._index,
                        $scope.event._id).success(function(data) {
                            $scope.eventdetail = data.objects;
                            $scope.comments = data.meta.comments;
                        })
                };
                $scope.postComment = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'comment',
                        $scope.formData.comment,
                        $scope.event._index,
                        $scope.event._id,
                        $scope.event._type).success(function(data) {
                            $scope.formData.comment = '';
                            $scope.commentForm.$setPristine();
                            $scope.comments.push(data['objects'][0]);
                            $scope.comment = true;
                        })
                };
            }
        }
    });

    module.directive('tsTimelineColor', function () {
        return {
            restrict: 'A',
            scope: {
                timelineColors: '=',
                indexId: '='
            },
            link: function (scope, elem, attrs) {
                elem.css("background", "#" + scope.timelineColors[scope.indexId])
            }
        }
    });

    module.directive('tsTimelineName', function () {
        return {
            restrict: 'E',
            scope: {
                timelineNames: '=',
                indexId: '='
            },
            link: function (scope, elem, attrs) {
                elem.text(scope.timelineNames[scope.indexId])
            }
        }
    });
})();

