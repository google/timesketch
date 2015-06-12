(function() {
    var module = angular.module('timesketch.core.upload.directive', []);

    module.directive('tsCoreUpload', ['timesketchApi', function (timesketchApi) {
        /**
         * Upload directive that handles the form and API call.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/core/core-upload.html',
            scope: {},
            controller: function($scope) {
                $scope.uploadForm = {};
                $scope.clearForm = function() {
                    $scope.uploadForm = {}
                };
                $scope.upload = function() {
                    console.log($scope.uploadForm)
                    if ($scope.uploadForm.name) {
                        timesketchApi.uploadFile($scope.uploadForm.file, $scope.uploadForm.name).success(function () {
                            $scope.uploadForm = {}
                        });
                    }
                }
            }
        };
    }]);

    module.directive('tsCoreFileModel', ['$parse', function ($parse) {
        /**
         * Make file input possible to bind to ng-model.
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

})();
