const path = require('path')
const webpack_config = require('./webpack.config.js')

const webpack_test_config = {
  entry: './main.spec.ts',
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: [
          'istanbul-instrumenter-loader',
          'ts-loader',
          'angular2-template-loader',
        ],
        exclude: /node_modules|\.spec\.ts/,
      },
      {
        test: /\.spec\.ts/,
        use: [
          'ts-loader',
          'angular2-template-loader',
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.s?css$/,
        use: 'null-loader',
      },
      {
        test: /\.html$/,
        loader: 'raw-loader',
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    modules: [path.resolve(__dirname, './'), 'node_modules'],
  },
}

module.exports = function(config) {
  config.set({
    files: [
      './node_modules/babel-polyfill/dist/polyfill.js',
      './main.spec.ts',
    ],
    preprocessors: {'./main.spec.ts': ['webpack']},
    webpack: webpack_test_config,
    webpackMiddleware: {
      noInfo: true,
      stats: {chunks: false},
    },
    frameworks: ['jasmine'],
    plugins: [
      require('karma-webpack'),
      require('karma-jasmine'),
      require('karma-phantomjs-launcher'),
      require('karma-coverage-istanbul-reporter'),
    ],
    browsers: ['PhantomJS'],
    reporters: ['progress', 'coverage-istanbul'],
    coverageIstanbulReporter: {
      reports: ['text-summary'],
      fixWebpackSourcePaths: false,
    }
  })
}
