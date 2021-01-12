var gulp = require('gulp');
var uglify = require('gulp-uglify');
var bump = require('gulp-bump');

gulp.task('default', ['compress']);

gulp.task('compress', function() {
    return gulp.src('jquery.tabletoCSV.js')
               .pipe(uglify())
               .pipe(gulp.dest('dist/'));
});

gulp.task('bump', function(){
    gulp.src('./*.json')
        .pipe(bump({type:'minor'}))
        .pipe(gulp.dest('./'));
});
