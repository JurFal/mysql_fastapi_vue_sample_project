# LaTeX文档编译Makefile

# 主文档名称（不含扩展名）
MAIN = algorithm_paper_template

# 默认目标
all: pdf zip

# 编译PDF
pdf:
	@echo "正在编译LaTeX文档..."
	xelatex $(MAIN).tex
	xelatex $(MAIN).tex
	xelatex $(MAIN).tex
	@echo "PDF编译完成: $(MAIN).pdf"

# 创建ZIP压缩包
zip: pdf
	@echo "正在创建ZIP压缩包..."
	zip -r $(MAIN).zip $(MAIN).tex references.bib $(MAIN).pdf Makefile README_latex.md
	@echo "ZIP压缩包创建完成: $(MAIN).zip"

# 清理临时文件
clean:
	@echo "正在清理临时文件..."
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "临时文件清理完成"

# 深度清理（包括PDF和ZIP）
clean-all: clean
	@echo "正在清理所有生成文件..."
	rm -f $(MAIN).pdf $(MAIN).zip
	@echo "所有生成文件清理完成"

# 快速编译（仅编译一次，适用于无参考文献的情况）
quick:
	@echo "正在快速编译LaTeX文档..."
	xelatex $(MAIN).tex
	@echo "快速编译完成: $(MAIN).pdf"

# 显示帮助信息
help:
	@echo "可用的命令:"
	@echo "  make pdf      - 编译生成PDF文档"
	@echo "  make zip      - 编译PDF并创建ZIP压缩包"
	@echo "  make clean    - 清理临时文件"
	@echo "  make clean-all - 清理所有生成文件"
	@echo "  make quick    - 快速编译（无参考文献）"
	@echo "  make help     - 显示此帮助信息"

.PHONY: all pdf zip clean clean-all quick help