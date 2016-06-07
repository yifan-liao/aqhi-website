module.exports = function (grunt) {
    grunt.initConfig({
        autoprefixer: {
            dist: {
                files: {
                    'aqhi/static/css/home.css': 'aqhi/static/css/home.css'
                }
            }
        },
        watch: {
            styles: {
                files: ['aqhi/static/css/home.css'],
                tasks: ['autoprefixer']
            }
        }
    });
    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-contrib-watch');
};