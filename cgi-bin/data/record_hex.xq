<files>
{
	for $file in doc("bamdata_amazon_links.xml")//file
	return
	<file>
	{
		<url>{data($file/@url)}</url>
	}
	{
		<colour>{data($file/@foreground)}</colour>
	}
	</file>
}
</files>