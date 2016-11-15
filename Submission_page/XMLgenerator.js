//This code taken from https://codepen.io/jon-walstedt/pen/jsIup

class XMLGenerator
  
  data: null
  addToExisting: false
  
  $document: null
  $fields: null
  $select: null
  $channelTemplate: null
  $itemTemplate: null
  $channelInfo: null
  $headerHelperOutput: null
  $output: null
  $addToExisting: null
  $itemsWrapper: null
  $items: null
  $addItem: null
  $removeItem: null
  $pubDate: null
  
  constructor: (@context) ->
    @data = {}
    @$document = $ document
    @$channelTemplate = $ "#channel-info-template"
    @$channelInfo = @context.find ".channel-info"
    @$fields = @context.find "input, textarea, select"
    @$select = @context.find "select"
    @$output = @context.find "#output"
    @$headerHelperOutput = @context.find ".header-helper-output"
    @$addToExisting = @context.find "#add-to-existing"
    @$itemsWrapper = @context.find ".item-wrapper"
    @$items = @context.find ".item"
    @$addItem = @context.find "#add-item"    
    @$selectCode = @context.find "#select-code"
    @$removeItem = @context.find ".remove-item"
    @$pubDate = @context.find ".item-pub-date"
    
    date = new Date()
    @$pubDate.val new Date(date.getTime())
    
    @resize()
      
    @addEventListeners()
    return
  
  addEventListeners: ()=>
    @$addItem.on "click", @onAddItemClick
    @$selectCode.on "click", @onSelectCodeClick
    @$document.on "click", @$removeItem, @onRemoveItemClick
    
    @$document.on "keyup", @$fields, @onKeyUp
    @$document.on "focus", "input, textarea, select", @addHelperText
    @$document.on "blur", "input, textarea, select", @removeHelperText
    #@$fields.on "focus", @addHelperText
    
    @$document.on "change", @$select, @onKeyUp
    @$addToExisting.on "change", @onAddToExistingChange
    
    $(window).on "resize", @onResize
    return

  addHelperText: (event) =>
    $field = $ event.target
    txt = $field.data "help-text"
    @$headerHelperOutput.html txt
    return
  
  removeHelperText: () =>
    @$headerHelperOutput.text ""
    return
  
  resize: () =>
    @$output.css
      height: $(window).height()-130
    return
  
  selectText: (element) =>
    doc = @$document.get(0)
    text = doc.getElementById element
    if doc.body.createTextRange
      range = doc.body.createTextRange()
      range.moveToElementText(text)
      range.select()
    else if window.getSelection
      selection = window.getSelection()
      range = doc.createRange()
      range.selectNodeContents text
      selection.removeAllRanges()
      selection.addRange range
      
    return
  
  
  onResize: (event) =>
    @resize()
    return
  
  onSelectCodeClick: (event) =>
    @selectText "output"
    return
  
  onAddItemClick: (event) =>
    $newItem = @$items.eq(0).clone()
    @$itemsWrapper.append $newItem
    return
  
 
  onRemoveItemClick: (event) =>
    $target = $ event.target
    if $target.hasClass "remove-item"
      $item = $target.closest ".item"
      $item.fadeOut "slow", ()=> $item.remove()
    return
  
  onAddToExistingChange: (event) =>
    if @$addToExisting.is(":checked")
      @addToExisting = true
      @$channelInfo.addClass "hide"
    else
      @addToExisting = false
      @$channelInfo.removeClass "hide"
    return
  
  onKeyUp: (event) =>
    @getData event
    @outputData()
    return
  
  getData: (event) =>
    $field = $ event.target
    val = $field.val()
    name = $field.attr "name"
    @data[name] = val
    
    arr = []
    for item in $(".item")
      $item = $ item
      obj = {}
      
      $input = $item.find(":input").not("button")

      for i in [0..$input.length] by 1
        $field = $ $input[i]
        inputName = $field.attr "name"
        obj[inputName] = $field.val()
      arr.push obj
    @data["items"] = arr
    return

  outputData: () =>
    source = @$channelTemplate.html()
    template = Handlebars.compile source
    umlautsString = @umlauts template(@data)
    xmlString = @htmlEncode umlautsString
    styledString = xmlString.replace(new RegExp("&lt;", 'g'), "<span class='node'>&lt;")
                            .replace(new RegExp("&gt;", 'g'), "&gt;</span>")


    @$output.html styledString
    return
  
  umlauts: (str) =>
    str = str.replace(new RegExp("å", 'g'), "&aring;")
                .replace(new RegExp("ä", 'g'), "&auml;")
                .replace(new RegExp("ö", 'g'), "&ouml;")
                .replace(new RegExp("Å", 'g'), "&Aring")
                .replace(new RegExp("Ä", 'g'), "&Auml;")
                .replace(new RegExp("Ö", 'g'), "&Ouml;")
    return str
  
  htmlEncode: (htmlString) =>
    return $('<div/>').text(htmlString).html()
  
  
generator = new XMLGenerator $ ".wrapper"