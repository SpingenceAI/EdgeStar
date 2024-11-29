from pydantic import BaseModel, Field
from typing import List


class SearchPlanStep(BaseModel):
    id: int = Field(description="Unique id of the step")
    step: str = Field(description="The step to perform")
    dependencies: List[int] = Field(
        description="List of step ids that this step depends on information from"
    )


class SearchQuery(BaseModel):
    query: str = Field(description="The search query")
    time_range: str = Field(
        description="The time range of the search query, e.g. month, year, week, day"
    )


class ResultData(BaseModel):
    search_query: str = Field(description="The search query")

    # search engine result
    url: str = Field(description="The url of the search result")
    title: str = Field(description="The title of the search result")
    content: str = Field(description="Part of the content of the search result")
    html_content: str = Field(
        description="The html content of the search result", default=""
    )
    body_markdown: str = Field(
        description="The body text of the search result in markdown format", default=""
    )
    body_text: str = Field(description="The body text of the search result", default="")
    concised_content: str = Field(
        description="The concised content of the search result", default=""
    )

    @property
    def reference_markdown(self):
        return f"[{self.title}]({self.url})"


class StepResult(BaseModel):
    id: int = Field(description="The id of the step")
    step: str = Field(description="The step name")
    results: List[ResultData] = Field(description="The search results")
    summary: str = Field(description="The summary of the step", default="")

    @property
    def results_text(self) -> str:
        content = f"Step {self.id}: {self.step}\n"
        if not self.results:
            return content + "No results"
        filtered_results = []
        for result in self.results:
            if result.concised_content not in [x.content for x in filtered_results]:
                filtered_results.append(result)
        for result in filtered_results:
            content += f"Title: {result.title}\n"
            content += f"URL: {result.url}\n"
            content += f"Content: {result.concised_content}\n"
        return content
