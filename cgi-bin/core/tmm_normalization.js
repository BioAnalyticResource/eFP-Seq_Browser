//=============================================================================
//
// Purpose: Calculate and performance TMM normalization
//
//=============================================================================
// This script is based off of Bioconductor's edgeR script: calcNormFactors.R
// https://github.com/Bioconductor-mirror/edgeR/blob/master/R/calcNormFactors.R

// WARNING: THIS SCRIPT IS INCOMPLETE AND NOT RECOMMENDED TO BE USED
// If redone, would just have used Math matrices for most the beginning of the code

var matrix_template;
/**
* Make a matrix based on input data
* @param {Any} data - Any dataset, recommend empty
* @param {Number} num_of_columns - Number of columns
* @param {Number} num_of_rows - Number of rows
* @return {Array} data - Matrix
*/
function make_matrix(data, num_of_columns, num_of_rows) {
  // code taken form: https://stackoverflow.com/questions/8301400/how-do-you-easily-create-empty-matrices-javascript
  data = [];
  var count = 1;
  for (var i = 0; i < num_of_columns; i++) {
    data[i] = [];
    for (var j = 0; j < num_of_rows; j++) {
      data[i][j] = count;
      count += 1
    }
  }
  return data;
}

var transpoing;
/**
* Transpose a matrix
* @param {Array} data - Matrix
* @return {Array} transpoing - Transposed matrix
*/
function transpose_matrix(data) {
  var og_num_cols = data.length;
  var og_num_rows = data[0].length;
  transpoing = [];
  for (var i = 0; i < og_num_rows; i++) {
    transpoing[i] = [];
    for (var j = 0; j < og_num_cols; j++) {
      transpoing[i][j] = data[j][i];
    }
  }
  return transpoing;
}

var divdedM;
/**
* Divide a matrix by a number
* @param {Number[]} data - Matrix
* @param {Number} divide_num - Number matrix divided by
* @return {Array} divdedM - Divided matrix
*/
function divide_matrix(data, divide_num) {
  var num_cols = data.length;
  var num_rows = data[0].length;
  divdedM = [];
  for (var i = 0; i < num_cols; i++) {
    divdedM[i] = [];
    for (var j = 0; j < num_rows; j++) {
      divdedM[i][j] = (parseFloat(data[i][j]) / parseFloat(divide_num));
    }
  }
  return divdedM;
}

/**
* Function to calculate library size if needed
* @param {Number[]} data - Matrix
* @param {Any} libsize - Library
* @return {List} calculating_libsize - List of what is included in the library
*/
function calcLibsize(data, libsize) {
  var calculating_libsize = [];
  var og_num_rows = data[0].length;
  for (var i = 0; i < data.length; i++) {
    var colSum = 0;
    for (var j = 0; j < og_num_rows; j++) {
      colSum += data[i][j];
    }
    calculating_libsize.push(colSum);
  }
  return calculating_libsize
}

/**
* Detemine factor quantile, mimicked from calcNormFactors.R's .calcFactorQuantile
* @param {Number[]} data - Matrix
* @param {Number} libsize - Library size
* @param {Number} p - Percentage value
* @return {Number[]} quantileMatrix - Quantile matrix
*/
function calcFactorQuantile(data, libsize, p) {
  var first_y = transpose_matrix(data);
  var second_y = divide_matrix(first_y, libsize);
  var third_y = transpose_matrix(second_y);

  var num_cols = data.length;
  var quantileMatrix = make_matrix(quantileMatrix, num_cols, 1);
  for (var i = 0; i < num_cols; i++) {
    for (var j = 0; j < 1; j++) {
      quantileMatrix[i][j] = math.quantileSeq(third_y[i], p);
    }
  }
  return quantileMatrix;
}

/**
* Creates a reference column which is required for factored weighting
* @param {Number[]} data - Matrix
* @param {Number} refColumn - Reference column length
* @return {Number[]} ref_matrix - Reference column matrix
*/
function switch_refColumn(data, refColumn) {
  var ref_output;
  if (refColumn == null) {
    refArray = [];
    for (var i = 0; i < data.length; i++) {
      for (var j = 0; j < 1; j++) {
        refArray.push(data[i][j]);
      }
    }
    refMean = math.mean(refArray);
    for (var i = 0; i < refArray.length; i++) {
      refArray[i] = Math.abs((refArray[i] - refMean));
    }
    refMin = math.min(refArray);
    refColumn = (refArray.indexOf(refMin) + 1);
    ref_output = refColumn;
  }
  else if (refColumn.length == 0 || refColumn < 1 || refColumn > data.length) {
    refColumn = 1;
    ref_output = refColumn;
  }
  var ref_matrix;
  ref_matrix = make_matrix(ref_matrix, 1, 1);
  ref_matrix[0][0] = ref_output;
  return ref_matrix;
}

/**
* Creates an empty matrix based on the data matrix which is required for factored weighting
* @param {Number[]} data - Matrix
* @return {Number[]} naArray - na matrix
*/
function switch_naArray(data) {
  var naArray = [];
  for (var i = 0; i < data.length; i++) {
    naArray.push("NA");
  }
  return naArray
}

/**
* Factored weighting to determine the TMM normalization, mimicked from calcNormFactors.R's .calcFactorQuantile, currently incomplete and not working
*/
function calcFactoredWeighted(obs, ref, libsize_obs, libsize_ref, logratioTrim, sumTrim, doWeighting, Acutoff) {
  if (logratioTrim == null) {
    logratioTrim = 0.3;
  }
  else if (logratioTrim != null) {
    logratioTrim = parseFloat(logratioTrim);
  }
  if (sumTrim == null) {
    sumTrim = 0.05;
  }
  else if (sumTrim != null) {
    sumTrim = parseFloat(sumTrim);
  }
  if (doWeighting == "false") {
    doWeighting = false;
  }
  else if (doWeighting == null || doWeighting == "true" || typeof(doWeighting) != "boolean") {
    doWeighting = true;
  }
  if (Acutoff == null) {
    Acutoff = parseFloat("-1e10");
  }
  else if (Acutoff != null) {
    Acutoff = parseFloat(Acutoff);
  }

  obs = convert_array(obs);
  ref = convert_array(ref);

  var n0;
  if (libsize_obs == null) {
    n0 = math.sum(obs);
  }
  var nR;
  if (libsize_ref == null) {
    nR = math.sum(ref);
  }

  // log ratio of expression, accounting for library size
  var obs_over_n0 = divide_arrays(obs, n0);
  var ref_over_nR = divide_arrays(ref, nR);
  var obsOn0_over_refOnR = divide_arrays(obs_over_n0, ref_over_nR);
  var logR = log2_array(obsOn0_over_refOnR);

  //absolute expression
  var log_obs_over_n0 = log2_array(obs_over_n0);
  var log_ref_over_nR = log2_array(ref_over_nR);
  var log_absolutes_add = addition_array(log_obs_over_n0, log_ref_over_nR);
  var absE = divide_array_by_num(log_absolutes_add, 2);

  //estimated asymptotic variances
  var n0_minus_obs = substraction_array(n0, obs);
  var n0_minus_obs_over_n0 = divide_arrays(n0_minus_obs, n0);
  var n0_minus_obs_over_n0_over_obs = divide_arrays(n0_minus_obs_over_n0, obs)
  var nR_minus_ref = substraction_array(nR, ref);
  var nR_minus_ref_over_nR = divide_arrays(nR_minus_ref, nR);
  var nR_minus_ref_over_nR_over_ref = divide_arrays(nR_minus_ref_over_nR, ref);
  var v = addition_array(n0_minus_obs_over_n0_over_obs, nR_minus_ref_over_nR_over_ref);

  //	remove infinite values, cutoff based on Acutoff
  var logR_finite = isFinite_array(logR);
  logR = isFinite_removal(logR, logR_finite);
  if (math.abs(math.max(logR)) < parseFloat("1e-6")) {
    var max_logR = math.abs(math.max(logR));
    logR[logR.indexOf(max_logR)] = 1;
  }
  var absE_finite = isFinite_array(absE);
  absE = isFinite_removal(absE, absE_finite);
  var v_finite = isFinite_array(v);
  v = isFinite_removal(v, v_finite);

  // taken from the original mean() function
  var n = logR.length;
  var loL = (math.floor(n * logratioTrim) + 1);
  var hiL = (n + 1 - loL);
  var loS = (math.floor(n * sumTrim) + 1);
  var hiS = (n + 1 - loS);

  //	keep <- (rank(logR) %in% loL:hiL) & (rank(absE) %in% loS:hiS)
  //	a fix from leonardo ivan almonacid cardenas, since rank() can return
  //	non-integer values when there are a lot of ties
  //  The following script is in R. Due to not knowing what rank does, cannot rewrite into JavaScript

  // keep <- (rank(logR)>=loL & rank(logR)<=hiL) & (rank(absE)>=loS & rank(absE)<=hiS)
  var f;
  if (doWeighting == true) {
    var narm = true;
    f = (math.sum(divide_arrays(logR, v)) + math.sum(divide_num_by_array(1, v)));
  }
  else if (doWeighting == false) {
    f = math.mean(logR);
  }

  //	Results will be missing if the two libraries share no features with positive counts
  //	In this case, return unity
  if (isNaN(f) == true) {
    f = 0;
  }
  else {
    f = Math.pow(2, f);
  }
}

// All functions were created to test and debug calcFactoredWeighted(), documentation will be added after it is completed

function convert_array(array) {
  for (i = 0; i < array.length; i++) {
    array[i] = parseFloat(array[i])
  }
}

function divide_arrays(numer, denom) {
  var results = [];
  for (i = 0; i < numer.length; i++) {
    results[i] = numer[i] / denom[i];
  }
  return results;
}

function divide_array_by_num(numer, num) {
  var results = [];
  for (i = 0; i < numer.length; i++) {
    results[i] = numer[i] / num;
  }
  return results;
}

function divide_num_by_array(num, denom) {
  var results = [];
  for (i = 0; i < denom.length; i++) {
    results[i] = num / denom[i];
  }
  return results;
}

function log2_arrays(array) {
  var results = [];
  for (i = 0; i < array.length; i++) {
    results[i] = Math.log2(array[i]);
  }
  return results;
}

function addition_array(array1, array2) {
  var results = [];
  for (i = 0; i < array1.length; i++) {
    results[i] = array1[i] + array2[i];
  }
  return results;
}

function addition_array_by_num(array1, num) {
  var results = [];
  for (i = 0; i < array1.length; i++) {
    results[i] = array1[i] + num;
  }
  return results;
}

function substraction_array(array1, array2) {
  var results = [];
  for (i = 0; i < array1.length; i++) {
    results[i] = array1[i] + array2[i];
  }
  return results;
}

function isFinite_array(array) {
  var results = [];
  for (i = 0; i < array.length; i++) {
    results[i] = isFinite(array[i]);
  }
  return results;
}

function isFinite_removal(num_array, finite_array) {
  var results = [];
  for (i = 0; i < num_array.length; i++) {
    if (finite_array[i] == false) {
      num_array[i] = "false"
    }
  }

  function removalFalse(value) {
    return value != "false";
  }

  var results = results.filter(removalFalse);
  return results;
}
