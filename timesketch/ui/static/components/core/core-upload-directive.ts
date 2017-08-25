import angular from 'angularjs-for-webpack'

(function() {
    var module = angular.module('timesketch.core.upload.directive', []);

    module.directive('tsCoreUpload', ['timesketchApi', '$rootScope', '$window', function (timesketchApi, $rootScope, $window) {
        /**
         * Upload directive that handles the form and API call.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/core/core-upload.html',
            scope: {
                sketchId: '=?',
                visible: '=?',
                btnText: '='
            },
            controller: function($scope) {
                $scope.uploadForm = {};
                $scope.clearForm = function() {
                    $scope.uploadForm = {}
                };
                // We need an integer here because Flask WTF form don't validate
                // undefined values.
                if (!$scope.sketchId) {
                    $scope.sketchId = 0;
                }
                $scope.uploadFile = function() {
                    if (!$scope.uploadForm.name) {
                        $scope.uploadForm.name = "";
                    }
                    timesketchApi.uploadFile($scope.uploadForm.file, $scope.uploadForm.name, $scope.sketchId).success(function () {
                        $scope.uploadForm = {};
                        $window.location.reload();
                    });
                };
            }
        };
    }]);

    module.directive('tsCoreFileModel', ['$parse', function ($parse) {
        /**
         * Bind the uploaded file (file object) to the scope.
         */
        return {
            restrict: 'A',
            scope: false,
            link: function(scope, element, attrs) {
                var model = $parse(attrs.tsCoreFileModel);
                var modelSetter = model.assign;

                element.bind('change', function(){
                    scope.$apply(function(){
                        modelSetter(scope, element[0].files[0]);
                    });
                });

            }
        };
    }]);

    module.directive('tsCoreUploadQueue', ['$interval', 'timesketchApi', function($interval, timesketchApi) {
        /**
         * Poll the API for active Celery tasks and render list.
         */
        // How often to poll the task API endpoint in milliseconds.
        var pollIntervall = 10000;
        return {
            restrict: 'E',
            templateUrl: '/static/components/core/core-upload-queue.html',
            scope: {},
            controller: function($scope) {
                var update_tasks = function() {
                    timesketchApi.getTasks().success(function (data) {
                        $scope.tasks = data['objects'];
                    });
                };
                update_tasks();
                $interval(function() {
                    update_tasks()
                }, pollIntervall);
            }
        };
    }]);

})();
