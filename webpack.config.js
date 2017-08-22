var path = require('path')

module.exports = {
 entry: './timesketch/ui/static/index.ts',
 module: {
   rules: [
     {
       test: /\.tsx?$/,
       use: 'ts-loader',
       exclude: /node_modules/,
     },
   ],
 },
 resolve: {
   extensions: ['.tsx', '.ts', '.js'],
   modules: [path.resolve(__dirname, 'timesketch/ui/static/'), 'node_modules'],
 },
 output: {
   filename: 'bundle.js',
   path: path.resolve(__dirname, 'timesketch/ui/static/'),
 },
}
