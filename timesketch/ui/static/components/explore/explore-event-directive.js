(function() {
    var module = angular.module('timesketch.explore.event.directive', []);

    module.directive('tsEvent', function () {
        return {
            restrict: 'A',
            templateUrl: '/static/components/explore/explore-event.html',
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
                        $scope.$parent.sketch.id,
                        'label',
                        '__ts_star',
                        $scope.event._index,
                        $scope.event._id).success(function(data) {})
                };
                $scope.getDetail = function() {
                    if ($scope.eventdetail) {return}
                    timesketchApi.getEvent(
                        $scope.$parent.sketch.id,
                        $scope.event._index,
                        $scope.event._id).success(function(data) {
                            $scope.eventdetail = data.objects;
                            $scope.comments = data.meta.comments;
                        })
                };
                $scope.postComment = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.$parent.sketch.id,
                        'comment',
                        $scope.formData.comment,
                        $scope.event._index,
                        $scope.event._id).success(function(data) {
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
            link: function (scope, elem, attrs) {
                var timeline_colors = scope.meta.timeline_colors;
                elem.css("background", "#" + timeline_colors[scope.event._index])
            }
        }
    });

    module.directive('tsTimelineName', function () {
        return {
            restrict: 'A',
            template: '<div class="label ts-name-label">{{meta.timeline_names[event._index]}}</div>'
        }
    });
})();

